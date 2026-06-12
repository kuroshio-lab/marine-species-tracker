"""Tests for the OBIS adapters: ``OBISSource`` and ``CursorTraversal``."""

from django.test import SimpleTestCase, TestCase

from species.models import CuratedObservation
from species.tasks.ingest import (
    CursorTraversal,
    DictResolver,
    IngestRun,
    OBISSource,
    PageContext,
    Rejection,
    ingest_source,
)


def _obis_record(**over):
    rec = {
        "id": "123",
        "decimalLongitude": -10.0,
        "decimalLatitude": 50.0,
        "eventDate": "2023-05-01",
        "scientificName": "Gadus morhua",
        "vernacularName": "atlantic cod",
        "basisOfRecord": "HumanObservation",
        "datasetName": "Test dataset",
    }
    rec.update(over)
    return rec


class _FakeOBISClient:
    """Returns pre-baked pages in call order (cursor walks forward)."""

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def fetch_occurrences(self, **kwargs):
        idx = len(self.calls)
        self.calls.append(kwargs)
        if idx < len(self.pages):
            return list(self.pages[idx]), 0
        return [], 0


class OBISSourceNormalizeTests(SimpleTestCase):
    def _norm(self, rec, taxonomy=None):
        return OBISSource().normalize(
            rec, taxonomy or DictResolver(), PageContext()
        )

    def test_uses_record_vernacular_title_cased(self):
        occ = self._norm(_obis_record())
        self.assertEqual(occ.common_name, "Atlantic Cod")
        self.assertEqual(occ.occurrence_id, "OBIS:123")
        self.assertEqual(occ.species_name, "Gadus morhua")

    def test_falls_back_to_taxonomy_when_no_vernacular(self):
        rec = _obis_record(vernacularName=None, aphiaID=126436)
        tax = DictResolver(common={126436: "european sprat"})
        occ = self._norm(rec, tax)
        self.assertEqual(occ.common_name, "European Sprat")

    def test_rejects_missing_coordinates(self):
        occ = self._norm(_obis_record(decimalLongitude=None))
        self.assertIsInstance(occ, Rejection)
        self.assertEqual(occ.reason, "no_coordinates")

    def test_rejects_missing_id(self):
        occ = self._norm(_obis_record(id=None))
        self.assertEqual(occ.reason, "no_id")

    def test_rejects_unparseable_date(self):
        occ = self._norm(_obis_record(eventDate=None))
        self.assertEqual(occ.reason, "no_date")


class CursorTraversalTests(SimpleTestCase):
    def test_next_cursor_is_last_record_id(self):
        client = _FakeOBISClient([[{"id": "7"}, {"id": "9"}]])
        traversal = CursorTraversal(client, geometry="POLY", sleep_seconds=0)
        page = traversal.fetch_page(None, 500)
        self.assertEqual(page.next_cursor, "9")
        self.assertEqual(len(page.records), 2)

    def test_empty_page_exhausts(self):
        client = _FakeOBISClient([[]])
        traversal = CursorTraversal(client, geometry="POLY", sleep_seconds=0)
        page = traversal.fetch_page(None, 500)
        self.assertIsNone(page.next_cursor)

    def test_cursor_paging_does_not_degrade(self):
        traversal = CursorTraversal(
            _FakeOBISClient([]), geometry="P", sleep_seconds=0
        )
        self.assertFalse(traversal.should_stop(IngestRun()))


class OBISFullRunTests(TestCase):
    def test_full_run_persists_with_title_cased_common_names(self):
        pages = [[
            _obis_record(id="1", occurrenceID="OBIS:1"),
            _obis_record(
                id="2",
                occurrenceID="OBIS:2",
                vernacularName=None,
                aphiaID=999,
            ),
        ]]
        client = _FakeOBISClient(pages)
        tax = DictResolver(common={999: "lesser weever"})
        run = ingest_source(
            OBISSource(),
            CursorTraversal(client, geometry="POLY", sleep_seconds=0),
            taxonomy=tax,
            page_size=500,
        )
        self.assertEqual(run.saved, 2)
        self.assertEqual(CuratedObservation.objects.count(), 2)
        self.assertEqual(
            CuratedObservation.objects.get(occurrence_id="OBIS:1").common_name,
            "Atlantic Cod",
        )
        self.assertEqual(
            CuratedObservation.objects.get(occurrence_id="OBIS:2").common_name,
            "Lesser Weever",
        )
