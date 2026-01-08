# species/tasks/gbif_etl.py
import logging
from django.contrib.gis.geos import Point
from django.db import transaction
from species.models import CuratedObservation
from .gbif_api import GBIFAPIClient
from .utils.etl_cleaning import (
    standardize_sex,
    parse_date_flexible,
    get_common_name_from_worms,
    to_float,
)

logger = logging.getLogger(__name__)

gbif_client = GBIFAPIClient(default_limit=300)


def passes_quality_check(record):
    """
    Hard quality filter: Only accept records with required fields.
    Returns: (passes: bool, rejection_reason: str)
    """
    # Coordinates
    if not record.get("decimalLatitude") or not record.get("decimalLongitude"):
        return False, "missing_coordinates"

    # Scientific name
    if not record.get("scientificName"):
        return False, "missing_species"

    # Date
    if not record.get("eventDate"):
        return False, "missing_date"

    return True, None


def fetch_and_store_gbif_data(
    geometry_wkt=None,
    taxon_key=None,
    year=None,
    limit=300,
    offset=0,
    strategy="obis_network",
):
    """
    Fetch GBIF occurrences with quality filters and deduplication.
    """
    logger.info(f"Starting GBIF ETL - strategy: {strategy}, offset: {offset}")

    try:
        # Fetch from GBIF
        gbif_records, total_count = gbif_client.fetch_occurrences(
            geometry=geometry_wkt,
            taxon_key=taxon_key,
            year=year,
            limit=limit,
            offset=offset,
            strategy=strategy,
        )

        if not gbif_records:
            return {"processed": 0, "saved": 0, "rejected": 0, "duplicates": 0}

        stats = {
            "processed": len(gbif_records),
            "saved": 0,
            "rejected": 0,
            "duplicates": 0,
            "rejection_reasons": {},
        }

        # Get existing occurrence_ids for dedup
        existing_occurrence_ids = set(
            CuratedObservation.objects.values_list("occurrence_id", flat=True)
        )

        with transaction.atomic():
            for record in gbif_records:
                # Quality check
                passes, reason = passes_quality_check(record)
                if not passes:
                    stats["rejected"] += 1
                    stats["rejection_reasons"][reason] = (
                        stats["rejection_reasons"].get(reason, 0) + 1
                    )
                    continue

                # Generate occurrence_id
                gbif_key = record.get("key")
                occurrence_id = (
                    record.get("occurrenceID") or f"GBIF:{gbif_key}"
                )

                # Deduplication
                if occurrence_id in existing_occurrence_ids:
                    stats["duplicates"] += 1
                    logger.debug(f"Skipping duplicate: {occurrence_id}")
                    continue

                # Parse coordinates
                try:
                    lat = float(record["decimalLatitude"])
                    lon = float(record["decimalLongitude"])
                    location = Point(lon, lat)
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Invalid coordinates for {occurrence_id}: {e}"
                    )
                    stats["rejected"] += 1
                    continue

                # Parse date
                observation_date = parse_date_flexible(record["eventDate"])
                if not observation_date:
                    stats["rejected"] += 1
                    continue

                # Depth normalization
                depth_min = to_float(record.get("minimumDepthInMeters"))
                depth_max = to_float(record.get("maximumDepthInMeters"))
                bathymetry = to_float(record.get("depth"))

                # If only one depth, use for both
                if depth_min and not depth_max:
                    depth_max = depth_min
                elif depth_max and not depth_min:
                    depth_min = depth_max

                # Common name from WoRMS
                common_name = get_common_name_from_worms(
                    record["scientificName"]
                )

                visibility = None
                notes = (
                    "Imported from GBIF dataset:"
                    f" {record.get('datasetName') or 'Unknown'}"
                )
                image = None
                validated = "validated"

                # Save to DB
                try:
                    CuratedObservation.objects.create(
                        occurrence_id=occurrence_id,
                        species_name=record["scientificName"],
                        common_name=common_name,
                        observation_date=observation_date,
                        location=location,
                        depth_min=depth_min,
                        depth_max=depth_max,
                        bathymetry=bathymetry,
                        temperature=to_float(record.get("waterTemperature")),
                        sex=standardize_sex(record.get("sex")),
                        visibility=visibility,
                        notes=notes,
                        image=image,
                        validated=validated,
                        source="GBIF",
                        dataset_name=record.get("datasetName", "")[:255],
                    )
                    stats["saved"] += 1
                    existing_occurrence_ids.add(occurrence_id)

                except Exception as e:
                    logger.error(
                        f"Failed to save GBIF record {occurrence_id}: {e}",
                        exc_info=True,
                    )
                    raise

        logger.info(
            f"GBIF ETL complete - Saved: {stats['saved']}, "
            f"Rejected: {stats['rejected']}, Duplicates: {stats['duplicates']}"
        )
        if stats["rejection_reasons"]:
            logger.info(f"Rejection breakdown: {stats['rejection_reasons']}")

        return stats

    except Exception as e:
        logger.error(f"GBIF ETL error: {e}", exc_info=True)
        raise
