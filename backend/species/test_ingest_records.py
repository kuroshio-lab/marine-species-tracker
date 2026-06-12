"""Tests for the inner ingestion seam: normalize -> dedup -> persist.

The interface is the test surface — a fake source, an in-memory taxonomy
resolver, and the test database. No network.
"""

from datetime import date

from django.contrib.gis.geos import Point
from django.test import TestCase

from species.models import CuratedObservation
from species.tasks.ingest import (
    CanonicalOccurrence,
    DictResolver,
    PageContext,
    Rejection,
    ingest_records,
)


class _DictSource:
    """Turns a raw dict straight into a canonical occurrence (or rejection)."""

    name = "OBIS"

    def identify(self, raw):
        return raw.get("occurrence_id")

    def normalize(self, raw, taxonomy, context):
        if "reject" in raw:
            return Rejection(raw["reject"])
        return CanonicalOccurrence(
            occurrence_id=raw["occurrence_id"],
            species_name=raw.get("species_name", "Testus marinus"),
            observation_date=date(2024, 1, 1),
            lon=raw.get("lon", 1.0),
            lat=raw.get("lat", 2.0),
            source="OBIS",
            common_name=raw.get("common_name"),
        )


def _ingest(records, seen=None):
    return ingest_records(
        _DictSource(),
        records,
        taxonomy=DictResolver(),
        seen=set() if seen is None else seen,
        context=PageContext(),
    )


class IngestRecordsTests(TestCase):
    def test_saves_new_records(self):
        result = _ingest([{"occurrence_id": "A"}, {"occurrence_id": "B"}])
        self.assertEqual(result.saved, 2)
        self.assertEqual(result.processed, 2)
        self.assertEqual(CuratedObservation.objects.count(), 2)

    def test_dedups_within_page(self):
        result = _ingest([{"occurrence_id": "A"}, {"occurrence_id": "A"}])
        self.assertEqual(result.saved, 1)
        self.assertEqual(result.duplicates, 1)
        self.assertEqual(CuratedObservation.objects.count(), 1)

    def test_dedups_against_seen(self):
        result = _ingest([{"occurrence_id": "A"}], seen={"A"})
        self.assertEqual(result.saved, 0)
        self.assertEqual(result.duplicates, 1)
        self.assertEqual(CuratedObservation.objects.count(), 0)

    def test_rejection_counted(self):
        result = _ingest([{"reject": "no_date"}, {"occurrence_id": "B"}])
        self.assertEqual(result.rejected, 1)
        self.assertEqual(result.saved, 1)

    def test_seen_record_is_duplicate_without_normalizing(self):
        # An already-seen id counts as a duplicate before normalization, so it
        # never triggers taxonomy resolution and is never miscounted as a
        # rejection when resolution would fail. (Without this, deep-offset
        # re-seen pages read as rejections and never trip should_stop.)
        class _CountingSource(_DictSource):
            def __init__(self):
                self.normalized = []

            def normalize(self, raw, taxonomy, context):
                self.normalized.append(raw.get("occurrence_id"))
                return Rejection("unresolved_name")

        source = _CountingSource()
        result = ingest_records(
            source,
            [{"occurrence_id": "A"}],
            taxonomy=DictResolver(),
            seen={"A"},
            context=PageContext(),
        )
        self.assertEqual(result.duplicates, 1)
        self.assertEqual(result.rejected, 0)
        self.assertEqual(source.normalized, [])

    def test_failed_persist_neither_aborts_page_nor_poisons_seen(self):
        # A row exists but is not in `seen`, so dedup misses it and the write
        # collides on the unique constraint. Its savepoint rolls back; the next
        # record still commits, and `seen` never gains the rolled-back id.
        CuratedObservation.objects.create(
            occurrence_id="X",
            species_name="Existing",
            observation_date=date(2020, 1, 1),
            location=Point(0.0, 0.0),
            source="OBIS",
        )
        seen = set()
        result = _ingest(
            [{"occurrence_id": "X"}, {"occurrence_id": "Y"}], seen=seen
        )
        self.assertEqual(result.saved, 1)
        self.assertEqual(result.rejected, 1)
        self.assertIn("Y", seen)
        self.assertNotIn("X", seen)
        self.assertEqual(CuratedObservation.objects.count(), 2)
