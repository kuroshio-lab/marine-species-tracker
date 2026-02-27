# species/tasks/obis_etl.py
import logging
import time
from typing import TypedDict

from django.conf import settings
from django.contrib.gis.geos import Point
from django.db import transaction

from species.models import CuratedObservation

from .obis_api import OBISAPIClient
from .utils.etl_cleaning import (
    clean_string_to_capital_capital,
    get_harmonized_common_name,
    normalize_obis_depth,
    parse_obis_event_date,
    standardize_sex,
    to_float,
)
from .worms_api import WoRMSAPIClient

logger = logging.getLogger(__name__)


class OBISETLResult(TypedDict):
    status: str
    records_processed: int
    new_records: int
    duplicates: int
    page: int


obis_client = OBISAPIClient(
    base_url=getattr(
        settings, "OBIS_API_BASE_URL", "https://api.obis.org/v3/"
    ),
    default_size=getattr(settings, "OBIS_API_DEFAULT_SIZE", 500),
    logger=logger,
)
worms_client = WoRMSAPIClient(
    base_url=getattr(
        settings, "WORMS_API_BASE_URL", "https://www.marinespecies.org/rest/"
    ),
    logger=logger,
)


def fetch_and_store_obis_data(
    geometry_wkt: str,
    taxonid: int | None = None,
    page: int = 0,
    start_date: str | None = None,
    end_date: str | None = None,
) -> OBISETLResult:
    """
    Fetch OBIS data and store with occurrence_id for deduplication.
    """
    logger.info(
        f"Starting OBIS ETL for geometry: {geometry_wkt}, taxonid: {taxonid}, "
        f"page: {page}, start_date: {start_date}, end_date: {end_date}"
    )

    try:
        obis_records, _ = obis_client.fetch_occurrences(
            geometry=geometry_wkt,
            taxonid=taxonid,
            page=page,
            start_date=start_date,
            end_date=end_date,
        )

        if not obis_records:
            logger.info("No OBIS records found")
            return {
                "status": "completed",
                "records_processed": 0,
                "new_records": 0,
                "duplicates": 0,
                "page": page,
            }

        new_records_count = 0
        skipped_count = 0

        # Get existing occurrence_ids for dedup
        existing_occurrence_ids = set(
            CuratedObservation.objects.values_list("occurrence_id", flat=True)
        )

        with transaction.atomic():
            for obs in obis_records:
                obis_id = obs.get("id")
                if not obis_id:
                    logger.warning(
                        f"OBIS record missing 'id' field, skipping: {obs}"
                    )
                    continue

                # Generate occurrence_id (OBIS uses 'id' as occurrenceID)
                occurrence_id = obs.get("occurrenceID") or f"OBIS:{obis_id}"

                # Deduplication check
                if occurrence_id in existing_occurrence_ids:
                    logger.debug(
                        f"Skipping duplicate occurrence_id: {occurrence_id}"
                    )
                    skipped_count += 1
                    continue

                # Coordinates required
                lon = obs.get("decimalLongitude")
                lat = obs.get("decimalLatitude")
                if lon is None or lat is None:
                    logger.warning(
                        f"OBIS record {obis_id} missing coordinates, skipping"
                    )
                    continue

                # Parse date
                event_date_str = obs.get("eventDate")
                observation_datetime, observation_date = parse_obis_event_date(
                    obis_id, event_date_str
                )
                if not observation_date:
                    logger.warning(
                        f"OBIS record {obis_id} missing valid date, skipping"
                    )
                    continue

                # Common name enrichment
                common_name = get_harmonized_common_name(obs, worms_client)

                # Machine Observation
                machine_observation_raw = obs.get("basisOfRecord")
                machine_observation = clean_string_to_capital_capital(
                    machine_observation_raw
                )

                # Depth normalization
                depth_min, depth_max, bathymetry = normalize_obis_depth(obs)

                # Temperature
                temperature = to_float(obs.get("sst"))

                visibility = None
                notes = (
                    "Imported from OBIS dataset:"
                    f" {obs.get('datasetName') or 'Unknown'}"
                )
                image = None
                validated = "validated"

                # Sex standardization
                sex = standardize_sex(obs.get("sex"))

                # Save to DB
                try:
                    CuratedObservation.objects.create(
                        occurrence_id=occurrence_id,
                        species_name=obs.get("scientificName")
                        or "Unknown species",
                        common_name=common_name,
                        observation_date=observation_date,
                        observation_datetime=observation_datetime,
                        location=Point(float(lon), float(lat)),
                        location_name=obs.get("datasetName") or "OBIS record",
                        machine_observation=machine_observation,
                        validated=validated,
                        depth_min=depth_min,
                        depth_max=depth_max,
                        bathymetry=bathymetry,
                        temperature=temperature,
                        visibility=visibility,
                        notes=notes,
                        image=image,
                        sex=sex,
                        source="OBIS",
                        dataset_name=obs.get("datasetName", "")[:255],
                    )
                    new_records_count += 1
                    existing_occurrence_ids.add(
                        occurrence_id
                    )  # Update in-memory set
                    logger.debug(
                        f"Saved OBIS record: {occurrence_id} -"
                        f" {obs.get('scientificName')}"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to save OBIS record {occurrence_id}: {e}",
                        exc_info=True,
                    )
                    raise

        logger.info(
            f"Finished OBIS ETL for page {page}. Processed:"
            f" {len(obis_records)}, New: {new_records_count}, Skipped:"
            f" {skipped_count}"
        )

        return {
            "status": "completed",
            "records_processed": len(obis_records),
            "new_records": new_records_count,
            "duplicates": skipped_count,
            "page": page,
        }

    except Exception as e:
        logger.error(f"Unhandled error in OBIS ETL: {e}", exc_info=True)
        raise


def trigger_full_obis_refresh(
    geometry_wkt: str,
    taxonid: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    max_pages: int | None = None,
) -> None:
    """
    Full or date-range OBIS refresh with pagination.
    """
    refresh_type = "incremental" if (start_date or end_date) else "full"
    print(
        f"Triggering {refresh_type} OBIS refresh for geometry: {geometry_wkt}"
    )

    page_size = obis_client.default_size

    # Get total record count
    initial_records, total_records = obis_client.fetch_occurrences(
        geometry=geometry_wkt,
        taxonid=taxonid,
        size=1,
        page=0,
        start_date=start_date,
        end_date=end_date,
    )

    if total_records == 0:
        print("No records found. Exiting.")
        return

    total_pages = (total_records + page_size - 1) // page_size
    print(f"Total records: {total_records}, estimated pages: {total_pages}")

    if max_pages is not None and max_pages < total_pages:
        print(f"Limiting to {max_pages} pages")
        total_pages = max_pages

    for page_num in range(total_pages):
        print(f"Processing page {page_num + 1} of {total_pages}...")
        fetch_and_store_obis_data(
            geometry_wkt,
            taxonid,
            page_num,
            start_date=start_date,
            end_date=end_date,
        )
        time.sleep(1)  # API rate limiting

    print(f"Finished {refresh_type} OBIS refresh.")
