# species/tasks/utils/etl_cleaning.py
import logging
import re
import pytz
from dateutil import parser
from datetime import datetime

logger = logging.getLogger(__name__)


def clean_string_to_capital_capital(input_string):
    """
    Cleans a string to "Capital Capital" format.
    """
    if not input_string:
        return None

    s = str(input_string)
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    s = re.sub(r"(human)(observation)", r"\1 \2", s, flags=re.IGNORECASE)
    s = re.sub(r"(machine)(observation)", r"\1 \2", s, flags=re.IGNORECASE)
    s = re.sub(r"(material)(sample)", r"\1 \2", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    cleaned_string = " ".join(
        [word.capitalize() for word in s.lower().split()]
    )

    return cleaned_string if cleaned_string else None


def to_float(value):
    """Safely convert to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def normalize_obis_depth(obs: dict):
    """Normalize OBIS depth fields."""
    raw_depth = obs.get("depth")
    raw_min = obs.get("minimumDepthInMeters")
    raw_max = obs.get("maximumDepthInMeters")
    raw_bathy = obs.get("bathymetry")

    depth = to_float(raw_depth)
    depth_min = to_float(raw_min)
    depth_max = to_float(raw_max)
    bathymetry = to_float(raw_bathy)

    if depth is not None:
        depth_min = depth_min if depth_min is not None else depth
        depth_max = depth_max if depth_max is not None else depth

    if depth_min is not None and depth_max is None:
        depth_max = depth_min
    if depth_max is not None and depth_min is None:
        depth_min = depth_max

    return depth_min, depth_max, bathymetry


def get_harmonized_common_name(obis_record, worms_client):
    """Get common name from OBIS or WoRMS."""
    obis_vernacular_name = obis_record.get("vernacularName")

    if obis_vernacular_name:
        return clean_string_to_capital_capital(obis_vernacular_name)
    else:
        aphia_id = obis_record.get("aphiaID")
        if aphia_id:
            worms_common_name = worms_client.get_common_name_by_aphia_id(
                aphia_id
            )
            return clean_string_to_capital_capital(worms_common_name)
    return None


def get_common_name_from_worms(scientific_name):
    """
    Get common name from WoRMS for GBIF records.
    Note: This is a simplified version. Full implementation would search by scientific name.
    """
    # TODO: Implement WoRMS search by scientific name
    # For now, return None - common names are optional
    return None


def parse_obis_event_date(obis_id: str, event_date_str: str):
    """Parse OBIS eventDate string."""
    observation_datetime = None
    observation_date = None

    if not event_date_str:
        logger.debug(f"OBIS record {obis_id} has no eventDate")
        return None, None

    try:
        dt_obj = parser.parse(event_date_str)
        if dt_obj.tzinfo is None or dt_obj.tzinfo.utcoffset(dt_obj) is None:
            observation_datetime = pytz.utc.localize(dt_obj)
        else:
            observation_datetime = dt_obj.astimezone(pytz.utc)
        observation_date = observation_datetime.date()
    except Exception as e:
        logger.warning(
            f"OBIS record {obis_id}: Failed to parse eventDate"
            f" '{event_date_str}': {e}"
        )

    return observation_datetime, observation_date


def parse_date_flexible(date_str):
    """
    Parse various date formats from GBIF/OBIS.
    Returns: date object or None
    """
    if not date_str:
        return None

    try:
        # Try parsing with dateutil
        dt_obj = parser.parse(date_str)
        return dt_obj.date()
    except Exception:
        # Try year-only format
        try:
            if len(date_str) == 4 and date_str.isdigit():
                return datetime(int(date_str), 1, 1).date()
        except Exception:
            pass

        logger.warning(f"Failed to parse date: {date_str}")
        return None


def standardize_sex(sex_value):
    """Standardize sex value."""
    if not sex_value:
        return "unknown"
    sex_value = str(sex_value).strip().lower()
    if sex_value in ["male", "m"]:
        return "male"
    elif sex_value in ["female", "f"]:
        return "female"
    else:
        return "unknown"
