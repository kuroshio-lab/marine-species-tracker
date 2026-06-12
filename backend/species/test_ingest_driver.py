"""Tests for the outer ingestion seam: the paging driver.

A fake traversal records the page sizes the driver requests, so the budget
behaviour (gate vs page-shrink) is asserted directly through the interface.
"""

from datetime import date

from django.test import TestCase

from species.tasks.ingest import (
    CanonicalOccurrence,
    DictResolver,
    Page,
    ingest_source,
)


class _DictSource:
    name = "OBIS"

    def identify(self, raw):
        return raw["occurrence_id"]

    def normalize(self, raw, taxonomy, context):
        return CanonicalOccurrence(
            occurrence_id=raw["occurrence_id"],
            species_name="Testus marinus",
            observation_date=date(2024, 1, 1),
            lon=1.0,
            lat=2.0,
            source="OBIS",
        )


class _ListTraversal:
    """Serves pre-baked pages and remembers every requested size."""

    def __init__(self, pages, should_stop=None):
        self.pages = pages  # list of (records, has_more)
        self._should_stop = should_stop or (lambda run: False)
        self.requested_sizes = []

    def fetch_page(self, cursor, size):
        idx = cursor or 0
        self.requested_sizes.append(size)
        records, has_more = self.pages[idx]
        next_cursor = (idx + 1) if has_more else None
        return Page(records=list(records)[:size], next_cursor=next_cursor)

    def should_stop(self, run):
        return self._should_stop(run)


def _recs(prefix, n):
    return [{"occurrence_id": f"{prefix}{i}"} for i in range(n)]


class DriverTests(TestCase):
    def _run(self, traversal, **kwargs):
        return ingest_source(
            _DictSource(), traversal, taxonomy=DictResolver(), **kwargs
        )

    def test_structural_exhaustion_stops_at_last_page(self):
        traversal = _ListTraversal(
            [(_recs("a", 3), True), (_recs("b", 2), False)]
        )
        run = self._run(traversal, page_size=10)
        self.assertEqual(run.pages, 2)
        self.assertEqual(run.saved, 5)

    def test_max_records_caps_and_shrinks_final_page(self):
        traversal = _ListTraversal(
            [(_recs("a", 10), True), (_recs("b", 10), True)]
        )
        run = self._run(traversal, page_size=10, max_records=5)
        self.assertEqual(run.saved, 5)
        self.assertEqual(traversal.requested_sizes, [5])
        self.assertEqual(run.pages, 1)

    def test_max_pages_caps_count_without_shrinking(self):
        traversal = _ListTraversal([
            (_recs("a", 10), True),
            (_recs("b", 10), True),
            (_recs("c", 10), True),
        ])
        run = self._run(traversal, page_size=10, max_pages=2)
        self.assertEqual(run.pages, 2)
        self.assertEqual(run.saved, 20)
        self.assertEqual(traversal.requested_sizes, [10, 10])

    def test_should_stop_ends_run_despite_more_pages(self):
        traversal = _ListTraversal(
            [(_recs("a", 3), True), (_recs("b", 3), True)],
            should_stop=lambda run: run.pages >= 1,
        )
        run = self._run(traversal, page_size=10)
        self.assertEqual(run.pages, 1)
        self.assertEqual(run.saved, 3)
