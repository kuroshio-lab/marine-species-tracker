# species/tasks/gbif_api.py
import logging
from pygbif import occurrences as occ

logger = logging.getLogger(__name__)


class GBIFAPIClient:
    def __init__(self, default_limit=300):
        self.default_limit = default_limit
        self.logger = logger

    def fetch_occurrences(self, **kwargs):
        """
        Flexible fetch from GBIF.
        Supports: year, geometry, taxonKey, limit, offset, depth, etc.
        """
        limit = kwargs.get("limit", self.default_limit)
        offset = kwargs.get("offset", 0)

        search_params = {
            "hasCoordinate": True,
            "hasGeospatialIssue": False,
            "limit": limit,
            "offset": offset,
        }

        # Merge all other filters (year, depth, etc.)
        search_params.update(kwargs)

        try:
            self.logger.info(f"GBIF API call: {search_params}")
            result = occ.search(**search_params)

            if not result or "results" not in result:
                return [], 0

            return result["results"], result.get("count", 0)
        except Exception as e:
            self.logger.error(f"GBIF API error: {e}", exc_info=True)
            return [], 0
