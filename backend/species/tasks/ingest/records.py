"""The inner seam: normalize -> dedup -> persist over one page of raw records.

This is the collapse. Given a ``Source``, a ``TaxonomyResolver``, the run's
``seen`` set, and the page context, it turns raw records into curated
observations. Its only ports are the taxonomy resolver (mock in tests) and the
database (test DB), so it is exercised end to end without the network.
"""

from __future__ import annotations

import logging

from django.contrib.gis.geos import Point
from django.db import transaction

from species.models import CuratedObservation

from .types import (
    CanonicalOccurrence,
    IngestResult,
    PageContext,
    Rejection,
    Source,
    TaxonomyResolver,
)

logger = logging.getLogger(__name__)


def ingest_records(
    source: Source,
    records: list[dict],
    *,
    taxonomy: TaxonomyResolver,
    seen: set[str],
    context: PageContext,
) -> IngestResult:
    """Normalize, dedup, and persist one page.

    ``seen`` is the run-level set of occurrence ids already written. It gains an
    id only after that record's savepoint commits, so a rolled-back write can
    never poison dedup for a later identical record in the same run.
    """
    result = IngestResult()
    for raw in records:
        result.processed += 1
        outcome = source.normalize(raw, taxonomy, context)
        if isinstance(outcome, Rejection):
            result.rejected += 1
            continue
        if outcome.occurrence_id in seen:
            result.duplicates += 1
            continue
        if _persist(outcome):
            seen.add(outcome.occurrence_id)
            result.saved += 1
        else:
            result.rejected += 1
    return result


def _persist(occ: CanonicalOccurrence) -> bool:
    """Write one canonical occurrence in its own savepoint.

    Returns ``True`` only when the row committed. Each record gets its own
    ``atomic()`` block so one bad record neither aborts the surrounding page
    (the old OBIS failure) nor poisons the transaction for the records after it
    (the old GBIF failure).
    """
    try:
        with transaction.atomic():
            CuratedObservation.objects.create(
                occurrence_id=occ.occurrence_id,
                species_name=occ.species_name,
                common_name=occ.common_name,
                observation_date=occ.observation_date,
                observation_datetime=occ.observation_datetime,
                location=Point(occ.lon, occ.lat),
                location_name=occ.location_name,
                machine_observation=occ.machine_observation,
                validated=occ.validated,
                depth_min=occ.depth_min,
                depth_max=occ.depth_max,
                bathymetry=occ.bathymetry,
                temperature=occ.temperature,
                notes=occ.notes,
                sex=occ.sex,
                source=occ.source,
                dataset_name=(occ.dataset_name or "")[:255],
            )
        return True
    except Exception as exc:
        logger.error(
            f"Failed to persist occurrence {occ.occurrence_id}: {exc}",
            exc_info=True,
        )
        return False
