import json

import requests


class OBISAPIClient:
    def __init__(
        self,
        base_url="https://api.obis.org/v3/",
        default_size=500,
        logger=None,
    ):
        self.base_url = base_url
        self.default_size = default_size
        self.logger = logger or self._get_default_logger()

    def _get_default_logger(self):
        import logging

        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def fetch_occurrences(
        self,
        geometry,
        taxonid=None,
        size=None,
        after=None,
        start_date=None,
        end_date=None,
    ):
        """
        Fetches occurrence data from OBIS API using cursor-based pagination.

        :param geometry: WKT polygon string
        :param taxonid: OBIS taxon ID (optional)
        :param size: Number of results per page (max 500)
        :param after: Cursor for pagination — the `id` of the last record from
            the previous page. Pass None (or omit) for the first request.
            The OBIS API uses cursor-based pagination, NOT offset-based.
            Passing `offset` silently breaks for large result sets.
        :param start_date: Date string (YYYY-MM-DD), eventDate >= this
        :param end_date: Date string (YYYY-MM-DD), eventDate <= this
        :return: Tuple (list of occurrence records, total count of records)
        """
        endpoint = f"{self.base_url}occurrence"
        params = {
            "geometry": geometry,
            "size": size or self.default_size,
        }
        if after is not None:
            params["after"] = after
        if taxonid:
            params["taxonid"] = taxonid
        if start_date:
            params["startdate"] = start_date
        if end_date:
            params["enddate"] = end_date

        self.logger.info(
            f"Fetching OBIS data from {endpoint} with params: {params}"
        )
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            total_count = data.get("total", 0)
            return data.get("results", []), total_count
        except requests.exceptions.RequestException as e:
            self.logger.error(f"OBIS API request failed: {e}")
            return [], 0
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON response from OBIS API.")
            return [], 0
