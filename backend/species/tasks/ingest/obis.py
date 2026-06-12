"""OBIS adapters: ``OBISSource`` (record normalizer) and ``CursorTraversal``
(``after``-cursor paging).

OBIS records already carry an ``aphiaID`` and often a ``vernacularName``, so
common-name harmonization prefers the record's own vernacular and falls back to
the taxonomy resolver. Cursor paging is reliable at any depth, so this traversal
never reports degradation.
"""

from __future__ import annotations

import time

from ..utils.etl_cleaning import (
    clean_string_to_capital_capital,
    normalize_obis_depth,
    parse_obis_event_date,
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


class OBISSource:
    """Normalizes an OBIS occurrence into a canonical occurrence."""

    name = "OBIS"

    def identify(self, raw: dict) -> str | None:
        return raw.get("occurrenceID") or f"OBIS:{raw.get('id')}"

    def normalize(
        self,
        raw: dict,
        taxonomy: TaxonomyResolver,
        context: PageContext,
    ) -> CanonicalOccurrence | Rejection:
        obis_id = raw.get("id")
        if not obis_id:
            return Rejection("no_id")

        lon = raw.get("decimalLongitude")
        lat = raw.get("decimalLatitude")
        if lon is None or lat is None:
            return Rejection("no_coordinates")

        observation_datetime, observation_date = parse_obis_event_date(
            obis_id, raw.get("eventDate")
        )
        if not observation_date:
            return Rejection("no_date")

        depth_min, depth_max, bathymetry = normalize_obis_depth(raw)
        dataset_name = raw.get("datasetName") or ""
        return CanonicalOccurrence(
            occurrence_id=raw.get("occurrenceID") or f"OBIS:{obis_id}",
            species_name=raw.get("scientificName") or "Unknown species",
            common_name=self._common_name(raw, taxonomy),
            observation_date=observation_date,
            observation_datetime=observation_datetime,
            lon=float(lon),
            lat=float(lat),
            source="OBIS",
            location_name=dataset_name or "OBIS record",
            machine_observation=clean_string_to_capital_capital(
                raw.get("basisOfRecord")
            ),
            depth_min=depth_min,
            depth_max=depth_max,
            bathymetry=bathymetry,
            temperature=to_float(raw.get("sst")),
            sex=standardize_sex(raw.get("sex")),
            dataset_name=dataset_name,
            notes=f"Imported from OBIS dataset: {dataset_name or 'Unknown'}",
        )

    @staticmethod
    def _common_name(raw: dict, taxonomy: TaxonomyResolver) -> str | None:
        vernacular = raw.get("vernacularName")
        if vernacular:
            return clean_string_to_capital_capital(vernacular)
        aphia_id = raw.get("aphiaID")
        if aphia_id:
            return clean_string_to_capital_capital(
                taxonomy.common_name(aphia_id)
            )
        return None


class CursorTraversal:
    """Walks OBIS pages with cursor (``after``) pagination.

    The cursor is the ``id`` of the last record on the previous page. Cursor
    paging does not degrade with depth, so ``should_stop`` is always ``False`` —
    the run ends when a page comes back empty (``next_cursor`` is ``None``).
    """

    def __init__(
        self,
        client,
        *,
        geometry,
        taxonid=None,
        start_date=None,
        end_date=None,
        sleep_seconds: float = 1.0,
        page_chunk_size: int | None = None,
    ) -> None:
        self.client = client
        self.geometry = geometry
        self.taxonid = taxonid
        self.start_date = start_date
        self.end_date = end_date
        self.sleep_seconds = sleep_seconds
        self.page_chunk_size = page_chunk_size
        self._pages_fetched = 0

    def fetch_page(self, cursor, size) -> Page:
        if self._should_pause():
            time.sleep(5)
        records, _ = self.client.fetch_occurrences(
            geometry=self.geometry,
            taxonid=self.taxonid,
            size=size,
            after=cursor,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self._pages_fetched += 1
        if self.sleep_seconds and records:
            time.sleep(self.sleep_seconds)
        next_cursor = str(records[-1]["id"]) if records else None
        return Page(records=records, next_cursor=next_cursor)

    def _should_pause(self) -> bool:
        return bool(
            self.page_chunk_size
            and self._pages_fetched
            and self._pages_fetched % self.page_chunk_size == 0
        )

    def should_stop(self, run: IngestRun) -> bool:
        return False
