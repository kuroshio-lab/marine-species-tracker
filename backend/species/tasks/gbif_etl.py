# species/tasks/gbif_etl.py
import logging
from typing import TypedDict

from django.contrib.gis.geos import Point as DjangoPoint
from django.db import transaction
from species.models import CuratedObservation
from .gbif_api import GBIFAPIClient
from .worms_api import WoRMSAPIClient
from shapely import wkt
from shapely.geometry import Point as ShapelyPoint
from .utils.etl_cleaning import (
    standardize_sex,
    parse_date_flexible,
    to_float,
    clean_scientific_name_for_worms_lookup,
)

logger = logging.getLogger(__name__)


class GBIFETLResult(TypedDict):
    processed: int
    saved: int
    rejected: int
    duplicates: int
    rejection_reasons: dict[str, int]


class GBIFOceanStats(TypedDict):
    saved: int
    processed: int


gbif_client = GBIFAPIClient(default_limit=300)
worms_client = WoRMSAPIClient()

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

# Cache to avoid redundant API calls during a single process run
_worms_cache = {}


def fetch_and_store_gbif_data(
    geometry_wkt: str | None = None,
    taxon_key: int | None = None,
    year: int | None = None,
    limit: int = 300,
    offset: int = 0,
    strategy: str = "obis_network",
    ocean_label: str | None = None,
) -> GBIFETLResult:
    """
    Main entry point for management commands. Supports year and enrichment.
    """
    stats = {
        "processed": 0,
        "saved": 0,
        "rejected": 0,
        "duplicates": 0,
        "rejection_reasons": {},
    }

    # Prep spatial filter
    poly_geom = wkt.loads(geometry_wkt) if geometry_wkt else None

    # GBIF API Call
    search_params = {
        "limit": limit,
        "offset": offset,
        "year": year,
        "depth": "1,11000",
    }
    if taxon_key:
        search_params["taxonKey"] = taxon_key
    if geometry_wkt and not poly_geom.bounds:
        search_params["geometry"] = geometry_wkt
    elif poly_geom:
        minx, miny, maxx, maxy = poly_geom.bounds
        search_params["decimalLatitude"] = f"{miny},{maxy}"
        search_params["decimalLongitude"] = f"{minx},{maxx}"

    gbif_records, _ = gbif_client.fetch_occurrences(**search_params)

    if not gbif_records:
        return stats

    existing_ids = set(
        CuratedObservation.objects.values_list("occurrence_id", flat=True)
    )

    with transaction.atomic():
        for rec in gbif_records:
            stats["processed"] += 1

            # 1. Spatial Check (Precise)
            lon, lat = rec.get("decimalLongitude"), rec.get("decimalLatitude")
            if lon is None or lat is None:
                continue
            if poly_geom and not poly_geom.contains(ShapelyPoint(lon, lat)):
                continue

            # 2. Deduplication
            occurrence_id = rec.get("occurrenceID") or f"GBIF:{rec.get('key')}"
            if occurrence_id in existing_ids:
                stats["duplicates"] += 1
                continue

            # 3. WoRMS Enrichment
            orig_name = rec.get("scientificName")
            if not orig_name:
                continue

            lookup_name = clean_scientific_name_for_worms_lookup(orig_name)
            if lookup_name not in _worms_cache:
                try:
                    aphia_id = worms_client.get_aphia_id_from_scientific_name(
                        lookup_name
                    )
                    cleaned_name = (
                        worms_client.get_scientific_name_by_aphia_id(aphia_id)
                        if aphia_id
                        else None
                    )
                    # MODIFIED LINE: ONLY take common name from WoRMS
                    common_name_from_worms = (
                        worms_client.get_common_name_by_aphia_id(aphia_id)
                        if aphia_id
                        else None
                    )

                    _worms_cache[lookup_name] = {
                        "cleaned_name": cleaned_name,
                        "common_name": common_name_from_worms,
                    }
                except Exception:
                    _worms_cache[lookup_name] = {
                        "cleaned_name": None,
                        "common_name": None,
                    }

            worms_data = _worms_cache[lookup_name]

            # Filter: Only save if we got a cleaned name from WoRMS
            if not worms_data["cleaned_name"]:
                stats["rejected"] += 1
                continue

            # 4. Save
            try:
                CuratedObservation.objects.create(
                    occurrence_id=occurrence_id,
                    species_name=worms_data["cleaned_name"],
                    common_name=worms_data["common_name"],
                    observation_date=parse_date_flexible(rec.get("eventDate")),
                    observation_datetime=rec.get("eventDate"),
                    location=DjangoPoint(lon, lat),
                    location_name=rec.get("locality")
                    or rec.get("waterBody")
                    or ocean_label
                    or "GBIF Import",
                    machine_observation=rec.get("basisOfRecord"),
                    source="GBIF",
                    depth_min=to_float(rec.get("depth"))
                    or to_float(rec.get("minimumDepthInMeters")),
                    depth_max=to_float(rec.get("depth"))
                    or to_float(rec.get("maximumDepthInMeters")),
                    sex=standardize_sex(rec.get("sex")),
                    dataset_name=rec.get("datasetName", "")[:255],
                    validated="validated",
                )
                stats["saved"] += 1
                existing_ids.add(occurrence_id)
            except Exception as e:
                logger.error(f"Save error {occurrence_id}: {e}")

    return stats


def sync_gbif_by_oceans(year: int | None = None, limit: int = 200) -> GBIFOceanStats:
    """
    Wrapper to run the ETL across all defined oceans.
    """
    overall_stats = {"saved": 0, "processed": 0}
    for name, wkt_str in OCEAN_POLYGONS_WKT.items():
        logger.info(f"Processing Ocean: {name} (Year: {year})")
        res = fetch_and_store_gbif_data(
            geometry_wkt=wkt_str, year=year, limit=limit, ocean_label=name
        )
        overall_stats["saved"] += res["saved"]
        overall_stats["processed"] += res["processed"]
    return overall_stats
