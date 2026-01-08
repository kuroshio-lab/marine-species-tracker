# species/tasks/deduplication.py
import logging
from species.models import CuratedObservation
from django.db.models import Count
from django.db import transaction

logger = logging.getLogger(__name__)


def find_duplicate_occurrence_ids():
    """
    Find occurrence_ids that exist in multiple records.
    Returns queryset of {occurrence_id, count}.
    """
    duplicates = (
        CuratedObservation.objects.values("occurrence_id")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )
    return duplicates


def merge_duplicate_records(
    occurrence_id, prefer_source="OBIS", dry_run=False
):
    """
    Merge records with same occurrence_id into one 'BOTH' record.

    Args:
        occurrence_id: The occurrence_id to merge
        prefer_source: Which source to keep as primary ('OBIS' or 'GBIF')
        dry_run: If True, don't actually save changes

    Returns:
        dict with merge stats
    """
    records = list(
        CuratedObservation.objects.filter(
            occurrence_id=occurrence_id
        ).order_by("source", "created_at")
    )

    if len(records) < 2:
        return {"action": "skip", "reason": "no_duplicates"}

    # Check if already marked as BOTH
    if any(r.source == "BOTH" for r in records):
        if not dry_run:
            keep = next(r for r in records if r.source == "BOTH")
            for r in records:
                if r.id != keep.id:
                    r.delete()
        return {"action": "cleaned", "kept_source": "BOTH"}

    # Identify primary and secondary
    obis_records = [r for r in records if r.source == "OBIS"]
    gbif_records = [r for r in records if r.source == "GBIF"]

    if prefer_source == "OBIS" and obis_records:
        primary = obis_records[0]
        secondary = gbif_records + obis_records[1:]
    elif prefer_source == "GBIF" and gbif_records:
        primary = gbif_records[0]
        secondary = obis_records + gbif_records[1:]
    else:
        # Fallback: use first record
        primary = records[0]
        secondary = records[1:]

    if dry_run:
        return {
            "action": "would_merge",
            "primary_source": primary.source,
            "secondary_sources": [s.source for s in secondary],
        }

    # Enrich primary with secondary data
    enrichment_fields = [
        "common_name",
        "observation_datetime",
        "depth_min",
        "depth_max",
        "bathymetry",
        "temperature",
        "sex",
        "dataset_name",
    ]

    with transaction.atomic():
        for sec in secondary:
            for field in enrichment_fields:
                primary_value = getattr(primary, field)
                secondary_value = getattr(sec, field)

                # Fill in missing fields
                if not primary_value and secondary_value:
                    setattr(primary, field, secondary_value)

        # Mark as BOTH
        primary.source = "BOTH"
        primary.save()

        # Delete secondary records
        for sec in secondary:
            sec.delete()

    logger.info(f"Merged {occurrence_id} into BOTH source")
    return {
        "action": "merged",
        "primary_source": prefer_source,
        "deleted_count": len(secondary),
    }
