# species/tasks/gbif_api.py
import logging
import time
from pygbif import occurrences as occ

logger = logging.getLogger(__name__)


class GBIFAPIClient:
    """
    Client for GBIF Occurrence API using pygbif.
    """

    def __init__(self, default_limit=300):
        self.default_limit = default_limit  # GBIF max is 300
        self.logger = logger

    def fetch_occurrences(
        self,
        geometry=None,
        taxon_key=None,
        year=None,
        limit=None,
        offset=0,
        strategy="obis_network",
    ):
        """
        Fetch marine occurrences from GBIF.

        Args:
            geometry: WKT polygon string
            taxon_key: GBIF taxon key (integer)
            year: Year or year range string (e.g., "2024" or "2023,2024")
            limit: Records per request (max 300)
            offset: Pagination offset
            strategy: "obis_network" or "marine_geographic"

        Returns:
            (records_list, total_count)
        """
        limit = limit or self.default_limit

        search_params = {
            "hasCoordinate": True,
            "hasGeospatialIssue": False,
            "limit": limit,
            "offset": offset,
        }

        # Strategy 1: OBIS network publishers only
        if strategy == "obis_network":
            search_params["networkKey"] = (
                "2b7c7b4f-4d4f-40d3-94de-c28b6fa054a6"
            )

        # Strategy 2: Geographic bounding box + mandatory depth
        elif strategy == "marine_geographic":
            if geometry:
                search_params["geometry"] = geometry
            search_params["depth"] = "0,11000"  # Any depth = marine

        # Optional filters
        if taxon_key:
            search_params["taxonKey"] = taxon_key
        if year:
            search_params["year"] = year

        try:
            self.logger.info(
                f"GBIF API call - strategy: {strategy}, offset: {offset}"
            )
            result = occ.search(**search_params)

            if not result or "results" not in result:
                self.logger.warning("No results from GBIF")
                return [], 0

            records = result["results"]
            total = result.get("count", 0)

            self.logger.info(
                f"GBIF returned {len(records)} records (total: {total})"
            )
            return records, total

        except Exception as e:
            self.logger.error(f"GBIF API error: {e}", exc_info=True)
            return [], 0
