"""The taxonomy resolver seam in front of WoRMS.

``WoRMSResolver`` hides both the HTTP transport and WoRMS's response-selection
policy (preferred-English vernacular, ``valid_name`` over ``scientificname``,
first match). ``DictResolver`` is the in-memory adapter tests use so
normalization never touches the network — two adapters justify the port.
"""

from __future__ import annotations

import json
import logging

import requests

logger = logging.getLogger(__name__)


class WoRMSResolver:
    """HTTP adapter for the WoRMS REST API.

    Each of the three lookups is memoized for the lifetime of the resolver,
    including negative results — a name that does not resolve is asked once, not
    once per occurrence. A single resolver is created per ingestion run, so the
    cache spans the whole run (the old per-run ``_worms_cache``).
    """

    def __init__(self, base_url: str | None = None, timeout: int = 10) -> None:
        from django.conf import settings

        self.base_url = base_url or getattr(
            settings,
            "WORMS_API_BASE_URL",
            "https://www.marinespecies.org/rest/",
        )
        self.timeout = timeout
        self._common_cache: dict = {}
        self._aphia_cache: dict = {}
        self._accepted_cache: dict = {}

    @staticmethod
    def _cached(cache: dict, key, compute):
        """Return ``compute()`` for ``key``, memoizing it — None included."""
        if key in cache:
            return cache[key]
        value = compute()
        cache[key] = value
        return value

    def _get(self, path: str):
        try:
            response = requests.get(
                f"{self.base_url}{path}", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except (
            requests.exceptions.RequestException,
            json.JSONDecodeError,
        ) as exc:
            logger.warning(f"WoRMS request failed for {path}: {exc}")
            return None

    def common_name(self, aphia_id):
        if not aphia_id:
            return None
        return self._cached(
            self._common_cache, aphia_id, lambda: self._fetch_common(aphia_id)
        )

    def _fetch_common(self, aphia_id):
        data = self._get(f"AphiaVernacularsByAphiaID/{aphia_id}")
        if not data:
            return None
        preferred = next(
            (
                d.get("vernacular")
                for d in data
                if d.get("language") == "English"
                and d.get("isPreferredName") == 1
                and d.get("vernacular")
            ),
            None,
        )
        if preferred:
            return preferred
        return next(
            (
                d.get("vernacular")
                for d in data
                if d.get("language") == "English" and d.get("vernacular")
            ),
            None,
        )

    def aphia_id(self, scientific_name):
        if not scientific_name:
            return None
        return self._cached(
            self._aphia_cache,
            scientific_name,
            lambda: self._fetch_aphia(scientific_name),
        )

    def _fetch_aphia(self, scientific_name):
        data = self._get(f"AphiaRecordsByName/{scientific_name}")
        if data:
            return data[0].get("AphiaID")
        return None

    def accepted_name(self, aphia_id):
        if not aphia_id:
            return None
        return self._cached(
            self._accepted_cache,
            aphia_id,
            lambda: self._fetch_accepted(aphia_id),
        )

    def _fetch_accepted(self, aphia_id):
        data = self._get(f"AphiaRecordByAphiaID/{aphia_id}")
        if data:
            return data.get("valid_name")
        return None


class DictResolver:
    """In-memory taxonomy resolver for tests."""

    def __init__(self, common=None, aphia=None, accepted=None) -> None:
        self._common = common or {}
        self._aphia = aphia or {}
        self._accepted = accepted or {}

    def common_name(self, aphia_id):
        return self._common.get(aphia_id)

    def aphia_id(self, scientific_name):
        return self._aphia.get(scientific_name)

    def accepted_name(self, aphia_id):
        return self._accepted.get(aphia_id)
