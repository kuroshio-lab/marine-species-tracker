"""Tests for the GBIF adapters: ``GBIFSource``, ``OffsetTraversal``,
``OceanFanout``."""

from django.test import SimpleTestCase, TestCase

from species.models import CuratedObservation
from species.tasks.ingest import (
    DictResolver,
    GBIFSource,
    IngestResult,
    IngestRun,
    OceanFanout,
    OffsetTraversal,
    PageContext,
    Rejection,
    ingest_source,
)
from species.tasks.ingest.gbif import OCEAN_POLYGONS_WKT


def _gbif_record(**over):
    rec = {
        "key": 42,
        "decimalLongitude": -20.0,
        "decimalLatitude": 30.0,
        "eventDate": "2023-06-15",
        "scientificName": "Funiculina quadrangularis (Pallas, 1766)",
        "basisOfRecord": "HUMAN_OBSERVATION",
    }
    rec.update(over)
    return rec


def _resolver():
    return DictResolver(
        aphia={"Funiculina quadrangularis": 128516},
        accepted={128516: "Funiculina quadrangularis"},
        common={128516: "tall sea pen"},
    )


class _FakeGBIFClient:
    def __init__(self, by_offset):
        self.by_offset = by_offset
        self.calls = []

    def fetch_occurrences(self, **kwargs):
        self.calls.append(kwargs)
        return list(self.by_offset.get(kwargs.get("offset", 0), [])), 0


class GBIFSourceNormalizeTests(SimpleTestCase):
    def _norm(self, rec, taxonomy=None, context=None):
        return GBIFSource().normalize(
            rec, taxonomy or _resolver(), context or PageContext()
        )

    def test_resolves_and_title_cases_common_name(self):
        occ = self._norm(_gbif_record())
        self.assertEqual(occ.species_name, "Funiculina quadrangularis")
        self.assertEqual(occ.common_name, "Tall Sea Pen")
        self.assertEqual(occ.occurrence_id, "GBIF:42")

    def test_rejects_unresolved_name(self):
        occ = self._norm(_gbif_record(), taxonomy=DictResolver())
        self.assertIsInstance(occ, Rejection)
        self.assertEqual(occ.reason, "unresolved_name")

    def test_rejects_missing_coordinates(self):
        occ = self._norm(_gbif_record(decimalLatitude=None))
        self.assertEqual(occ.reason, "no_coordinates")

    def test_rejects_missing_name(self):
        occ = self._norm(_gbif_record(scientificName=None))
        self.assertEqual(occ.reason, "no_name")

    def test_ocean_label_is_location_name_fallback(self):
        occ = self._norm(
            _gbif_record(), context=PageContext(ocean_label="Indian_Ocean")
        )
        self.assertEqual(occ.location_name, "Indian_Ocean")

    def test_locality_wins_over_ocean_label(self):
        occ = self._norm(
            _gbif_record(locality="Bay of Biscay"),
            context=PageContext(ocean_label="North_Atlantic"),
        )
        self.assertEqual(occ.location_name, "Bay of Biscay")


class OffsetTraversalTests(SimpleTestCase):
    def test_full_page_advances_offset(self):
        client = _FakeGBIFClient({0: [_gbif_record(key=i) for i in range(3)]})
        page = OffsetTraversal(client).fetch_page(0, 3)
        self.assertEqual(page.next_cursor, 3)

    def test_short_page_exhausts(self):
        client = _FakeGBIFClient({0: [_gbif_record(key=1)]})
        page = OffsetTraversal(client).fetch_page(0, 3)
        self.assertIsNone(page.next_cursor)

    def test_should_stop_on_deep_offset_duplicates(self):
        traversal = OffsetTraversal(_FakeGBIFClient({}))
        run = IngestRun()
        run.add(
            IngestResult(processed=10, saved=0, duplicates=9), requested=10
        )
        self.assertTrue(traversal.should_stop(run))

    def test_should_not_stop_while_still_saving(self):
        traversal = OffsetTraversal(_FakeGBIFClient({}))
        run = IngestRun()
        run.add(
            IngestResult(processed=10, saved=2, duplicates=8), requested=10
        )
        self.assertFalse(traversal.should_stop(run))


class OceanFanoutTests(SimpleTestCase):
    def test_walks_every_ocean_in_order_and_tags_label(self):
        client = _FakeGBIFClient({0: []})
        traversal = OceanFanout(client, OCEAN_POLYGONS_WKT, year=2023)
        labels, cursor, page = [], 0, None
        for _ in range(len(OCEAN_POLYGONS_WKT)):
            page = traversal.fetch_page(cursor, 50)
            labels.append(page.context.ocean_label)
            if page.next_cursor is None:
                break
            cursor = page.next_cursor
        self.assertEqual(labels, list(OCEAN_POLYGONS_WKT.keys()))
        self.assertIsNone(page.next_cursor)

    def test_filters_records_outside_the_polygon(self):
        arctic = {"Arctic_Ocean": OCEAN_POLYGONS_WKT["Arctic_Ocean"]}
        inside = _gbif_record(
            key=1, decimalLatitude=80.0, decimalLongitude=0.0
        )
        outside = _gbif_record(
            key=2, decimalLatitude=0.0, decimalLongitude=0.0
        )
        client = _FakeGBIFClient({0: [inside, outside]})
        page = OceanFanout(client, arctic).fetch_page(0, 50)
        self.assertEqual([r["key"] for r in page.records], [1])


class GBIFFullRunTests(TestCase):
    def test_offset_run_persists_resolved_and_title_cased(self):
        client = _FakeGBIFClient({0: [_gbif_record(key=1)]})
        run = ingest_source(
            GBIFSource(),
            OffsetTraversal(client),
            taxonomy=_resolver(),
            page_size=3,
        )
        self.assertEqual(run.saved, 1)
        obs = CuratedObservation.objects.get(occurrence_id="GBIF:1")
        self.assertEqual(obs.species_name, "Funiculina quadrangularis")
        self.assertEqual(obs.common_name, "Tall Sea Pen")
        self.assertEqual(obs.source, "GBIF")
