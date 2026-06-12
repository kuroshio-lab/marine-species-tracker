"""GBIF adapters: ``GBIFSource`` (record normalizer) and two traversals —
``OffsetTraversal`` (offset paging, the only traversal that degrades) and
``OceanFanout`` (one single-shot page per ocean polygon).

GBIF records carry no ``aphiaID``, so common-name and accepted-name come from
the taxonomy resolver: clean the scientific name, resolve it to an AphiaID, take
WoRMS's accepted name, and reject the record if it does not resolve. The two
traversals share one ``GBIFSource`` — that is the split the ``if strategy ==
'oceans'`` branch used to hide.
"""

from __future__ import annotations

import time

from dateutil import parser as date_parser
from django.utils import timezone
from shapely import wkt
from shapely.geometry import Point as ShapelyPoint

from ..utils.etl_cleaning import (
    clean_scientific_name_for_worms_lookup,
    clean_string_to_capital_capital,
    parse_date_flexible,
    standardize_sex,
    to_float,
)
from .types import (
    CanonicalOccurrence,
    IngestRun,
    Page,
    PageContext,
    Rejection,
    TaxonomyResolver,
)

OCEAN_POLYGONS_WKT = {
    "Arctic_Ocean": "POLYGON((-180 65, 180 65, 180 90, -180 90, -180 65))",
    "North_Atlantic": "POLYGON((-80 0, -10 0, -10 65, -80 65, -80 0))",
    "South_Atlantic": "POLYGON((-60 -60, 20 -60, 20 0, -60 0, -60 -60))",
    "Indian_Ocean": "POLYGON((20 -60, 120 -60, 120 25, 20 25, 20 -60))",
    "West_Pacific": "POLYGON((120 -60, 180 -60, 180 65, 120 65, 120 -60))",
    "North_East_Pacific": "POLYGON((-180 0, -80 0, -80 65, -180 65, -180 0))",
    "South_East_Pacific": (
        "POLYGON((-180 -60, -67 -60, -75 -50, -72 -40, -70 -30, -70 -20, -80"
        " -10, -80 0, -180 0, -180 -60))"
    ),
    "Southern_Ocean": (
        "POLYGON((-180 -90, 180 -90, 180 -60, -180 -60, -180 -90))"
    ),
}

DEEP_OFFSET_DUPLICATE_RATIO = 0.8


class GBIFSource:
    """Normalizes a GBIF occurrence into a canonical occurrence."""

    name = "GBIF"

    def identify(self, raw: dict) -> str | None:
        return raw.get("occurrenceID") or f"GBIF:{raw.get('key')}"

    def normalize(
        self,
        raw: dict,
        taxonomy: TaxonomyResolver,
        context: PageContext,
    ) -> CanonicalOccurrence | Rejection:
        lon = raw.get("decimalLongitude")
        lat = raw.get("decimalLatitude")
        if lon is None or lat is None:
            return Rejection("no_coordinates")

        orig_name = raw.get("scientificName")
        if not orig_name:
            return Rejection("no_name")

        lookup_name = clean_scientific_name_for_worms_lookup(orig_name)
        aphia_id = taxonomy.aphia_id(lookup_name)
        accepted_name = taxonomy.accepted_name(aphia_id) if aphia_id else None
        if not accepted_name:
            return Rejection("unresolved_name")

        observation_date = parse_date_flexible(raw.get("eventDate"))
        if not observation_date:
            return Rejection("no_date")

        return CanonicalOccurrence(
            occurrence_id=raw.get("occurrenceID") or f"GBIF:{raw.get('key')}",
            species_name=accepted_name,
            common_name=clean_string_to_capital_capital(
                taxonomy.common_name(aphia_id)
            ),
            observation_date=observation_date,
            observation_datetime=_to_datetime(raw.get("eventDate")),
            lon=float(lon),
            lat=float(lat),
            source="GBIF",
            location_name=(
                raw.get("locality")
                or raw.get("waterBody")
                or context.ocean_label
                or "GBIF Import"
            ),
            machine_observation=raw.get("basisOfRecord"),
            depth_min=to_float(raw.get("depth"))
            or to_float(raw.get("minimumDepthInMeters")),
            depth_max=to_float(raw.get("depth"))
            or to_float(raw.get("maximumDepthInMeters")),
            sex=standardize_sex(raw.get("sex")),
            dataset_name=raw.get("datasetName") or "",
        )


class OffsetTraversal:
    """Walks GBIF pages with offset pagination over one query geometry.

    Offset paging degrades past large offsets — GBIF starts returning records
    already ingested — so ``should_stop`` ends the run when a full page comes
    back saving nothing and mostly duplicates.
    """

    def __init__(
        self,
        client,
        *,
        geometry_wkt=None,
        taxon_key=None,
        year=None,
        ocean_label=None,
        sleep_seconds: float = 0.5,
    ) -> None:
        self.client = client
        self.geometry_wkt = geometry_wkt
        self.taxon_key = taxon_key
        self.year = year
        self.ocean_label = ocean_label
        self.sleep_seconds = sleep_seconds
        self._poly = wkt.loads(geometry_wkt) if geometry_wkt else None

    def fetch_page(self, cursor, size) -> Page:
        offset = cursor or 0
        # Be nice to GBIF: pause between successive page fetches, but not
        # before the first (offset 0).
        if offset and self.sleep_seconds:
            time.sleep(self.sleep_seconds)
        params = _gbif_params(
            self._poly,
            self.geometry_wkt,
            self.taxon_key,
            self.year,
            size,
            offset,
        )
        raw, _ = self.client.fetch_occurrences(**params)
        next_cursor = (offset + size) if len(raw) == size else None
        return Page(
            records=_within(self._poly, raw),
            next_cursor=next_cursor,
            context=PageContext(ocean_label=self.ocean_label),
        )

    def should_stop(self, run: IngestRun) -> bool:
        last = run.last
        if last is None:
            return False
        # Deep-offset degradation is only diagnosable from a full offset page.
        # When max_records shrinks the page to fit the remaining budget
        # (last_requested < page_size), an all-duplicate page is the budget
        # tail, not GBIF replaying ingested records — e.g. --max-records 1
        # requests a single record, and one duplicate must not stop paging at
        # offset 0. Gate on a full page so the ratio denominator is meaningful.
        if run.page_size and run.last_requested < run.page_size:
            return False
        return (
            last.saved == 0
            and last.duplicates
            > DEEP_OFFSET_DUPLICATE_RATIO * run.last_requested
        )


class OceanFanout:
    """Queries each ocean polygon once instead of paging by offset.

    Each page is one ocean's single-shot result, tagged with its ocean label so
    the source can use it as the ``location_name`` fallback. Single-shot fan-out
    does not degrade, so ``should_stop`` is always ``False``.
    """

    def __init__(self, client, ocean_polygons, *, year=None) -> None:
        self.client = client
        self.oceans = list(ocean_polygons.items())
        self.year = year

    def fetch_page(self, cursor, size) -> Page:
        index = cursor or 0
        if index >= len(self.oceans):
            return Page(records=[], next_cursor=None)
        label, wkt_str = self.oceans[index]
        poly = wkt.loads(wkt_str)
        params = _gbif_params(poly, wkt_str, None, self.year, size, 0)
        raw, _ = self.client.fetch_occurrences(**params)
        next_index = index + 1
        next_cursor = next_index if next_index < len(self.oceans) else None
        return Page(
            records=_within(poly, raw),
            next_cursor=next_cursor,
            context=PageContext(ocean_label=label),
        )

    def should_stop(self, run: IngestRun) -> bool:
        return False


def _gbif_params(poly, geometry_wkt, taxon_key, year, limit, offset) -> dict:
    params = {
        "limit": limit,
        "offset": offset,
        "year": year,
        "depth": "1,11000",
    }
    if taxon_key:
        params["taxonKey"] = taxon_key
    if geometry_wkt and poly is not None and not poly.bounds:
        params["geometry"] = geometry_wkt
    elif poly is not None:
        minx, miny, maxx, maxy = poly.bounds
        params["decimalLatitude"] = f"{miny},{maxy}"
        params["decimalLongitude"] = f"{minx},{maxx}"
    return params


def _within(poly, raw: list[dict]) -> list[dict]:
    """Keep records inside ``poly``.

    The GBIF query is a bounding box around the polygon, so the precise polygon
    filter runs here. Records missing coordinates are kept so the source can
    reject them — that keeps ``processed`` honest. Filtering may empty a page
    while more pages remain, which is why the driver ends on ``next_cursor``,
    not on the record count.
    """
    if poly is None:
        return list(raw)
    kept = []
    for rec in raw:
        lon = rec.get("decimalLongitude")
        lat = rec.get("decimalLatitude")
        if lon is None or lat is None:
            kept.append(rec)
            continue
        if poly.contains(ShapelyPoint(lon, lat)):
            kept.append(rec)
    return kept


def _to_datetime(event_date: str | None):
    """Parse a GBIF eventDate into a timezone-aware datetime, or None.

    ``USE_TZ`` is on, so a naive datetime would warn on save; assume UTC when
    GBIF gives no offset.
    """
    if not event_date:
        return None
    try:
        parsed = date_parser.parse(event_date)
    except (ValueError, OverflowError, TypeError):
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed)
    return parsed
