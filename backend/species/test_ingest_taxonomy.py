"""Tests for WoRMSResolver memoization (including negative results) and the
configurable inter-page delay on OffsetTraversal."""
from unittest import mock

from django.test import SimpleTestCase

from species.tasks.ingest import OffsetTraversal, WoRMSResolver


def _response(payload):
    resp = mock.Mock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


class WoRMSResolverCacheTests(SimpleTestCase):
    def test_common_name_lookup_is_cached(self):
        payload = [
            {
                "language": "English",
                "isPreferredName": 1,
                "vernacular": "Tall Sea Pen",
            }
        ]
        with mock.patch(
            "species.tasks.ingest.taxonomy.requests.get",
            return_value=_response(payload),
        ) as get:
            resolver = WoRMSResolver()
            self.assertEqual(resolver.common_name(128516), "Tall Sea Pen")
            self.assertEqual(resolver.common_name(128516), "Tall Sea Pen")
            self.assertEqual(get.call_count, 1)

    def test_negative_results_are_cached(self):
        # No data resolves to None; the None must be remembered, not re-asked.
        with mock.patch(
            "species.tasks.ingest.taxonomy.requests.get",
            return_value=_response([]),
        ) as get:
            resolver = WoRMSResolver()
            self.assertIsNone(resolver.aphia_id("Nonexistent species"))
            self.assertIsNone(resolver.aphia_id("Nonexistent species"))
            self.assertEqual(get.call_count, 1)

    def test_accepted_name_lookup_is_cached(self):
        with mock.patch(
            "species.tasks.ingest.taxonomy.requests.get",
            return_value=_response({"valid_name": "Funiculina"}),
        ) as get:
            resolver = WoRMSResolver()
            resolver.accepted_name(128516)
            resolver.accepted_name(128516)
            self.assertEqual(get.call_count, 1)


class OffsetTraversalDelayTests(SimpleTestCase):
    def _client(self):
        client = mock.Mock()
        client.fetch_occurrences.return_value = ([], 0)
        return client

    def test_no_delay_before_first_page(self):
        traversal = OffsetTraversal(self._client(), sleep_seconds=0.01)
        with mock.patch("species.tasks.ingest.gbif.time.sleep") as sleep:
            traversal.fetch_page(0, 300)
            sleep.assert_not_called()

    def test_delay_between_subsequent_pages(self):
        traversal = OffsetTraversal(self._client(), sleep_seconds=0.01)
        with mock.patch("species.tasks.ingest.gbif.time.sleep") as sleep:
            traversal.fetch_page(300, 300)
            sleep.assert_called_once_with(0.01)
