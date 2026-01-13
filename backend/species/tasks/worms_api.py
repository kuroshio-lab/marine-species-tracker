import json

import requests


class WoRMSAPIClient:
    def __init__(
        self, base_url="https://www.marinespecies.org/rest/", logger=None
    ):
        self.base_url = base_url
        self.logger = logger or self._get_default_logger()

    def _get_default_logger(self):
        import logging

        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def get_common_name_by_aphia_id(self, aphia_id):
        """
        Fetches common names for a given AphiaID from WoRMS.
        :param aphia_id: The AphiaID (integer)
        :return: Preferred common name (string) or None
        """
        if not aphia_id:
            return None

        endpoint = f"{self.base_url}AphiaVernacularsByAphiaID/{aphia_id}"
        self.logger.debug(f"Fetching WoRMS common name from {endpoint}")
        try:
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                # Prioritize preferred English name
                preferred_english = next(
                    (
                        d.get("vernacular")
                        for d in data
                        if d.get("language") == "English"
                        and d.get("isPreferredName") == 1
                        and d.get("vernacular")
                    ),
                    None,
                )
                if preferred_english:
                    return preferred_english

                # If no preferred, take the first available English name
                first_english = next(
                    (
                        d.get("vernacular")
                        for d in data
                        if d.get("language") == "English"
                        and d.get("vernacular")
                    ),
                    None,
                )
                return first_english
            return None
        except requests.exceptions.RequestException as e:
            self.logger.warning(
                f"WoRMS API request failed for AphiaID {aphia_id}: {e}"
            )
            return None
        except json.JSONDecodeError:
            self.logger.warning(
                "Failed to decode JSON response from WoRMS API for AphiaID"
                f" {aphia_id}."
            )
            return None

    def get_aphia_id_from_scientific_name(self, scientific_name):
        """
        Fetches the AphiaID for a given scientific name from WoRMS.
        :param scientific_name: The scientific name string (e.g., "Dendronotus elegans A.E.Verrill, 1880")
        :return: AphiaID (integer) or None
        """
        if not scientific_name:
            return None

        # WoRMS API for matching names
        endpoint = f"{self.base_url}AphiaRecordsByName/{scientific_name}"
        self.logger.debug(
            f"Fetching AphiaID for '{scientific_name}' from {endpoint}"
        )
        try:
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0].get("AphiaID")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.warning(
                "WoRMS API request failed for scientific name"
                f" '{scientific_name}': {e}"
            )
            return None
        except json.JSONDecodeError:
            self.logger.warning(
                "Failed to decode JSON response from WoRMS API for scientific"
                f" name '{scientific_name}'."
            )
            return None

    def get_scientific_name_by_aphia_id(self, aphia_id):
        """
        Fetches the scientific name (often cleaner, without author/year) for a given AphiaID from WoRMS.
        :param aphia_id: The AphiaID (integer)
        :return: Cleaned scientific name (string) or None
        """
        if not aphia_id:
            return None

        # WoRMS API for getting a record by AphiaID
        endpoint = f"{self.base_url}AphiaRecordByAphiaID/{aphia_id}"
        self.logger.debug(
            f"Fetching scientific name for AphiaID {aphia_id} from {endpoint}"
        )
        try:
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                # 'scientificname' often includes author and year.
                # 'valid_name' is usually the accepted scientific name without author/year,
                # which is what you're looking for to "clean" it.
                return data.get("valid_name")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.warning(
                f"WoRMS API request failed for AphiaID {aphia_id}: {e}"
            )
            return None
        except json.JSONDecodeError:
            self.logger.warning(
                "Failed to decode JSON response from WoRMS API for AphiaID"
                f" {aphia_id}."
            )
            return None
