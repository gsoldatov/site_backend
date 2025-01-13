"""
Data converting functions for preparing JSON responses.
"""
from datetime import datetime, timezone
import json

from backend_main.validation.util import RequestValidationException


def row_proxy_to_dict(row_proxy):
    """
    Converts SQLAlchemy RowProxy object into a dict.
    datetime fields are converted into strings.
    """
    result = {}
    for k in row_proxy:
        if type(row_proxy[k]) == datetime:
            result[k] = row_proxy[k].isoformat()
        else:
            result[k] = row_proxy[k]
    return result


def error_json(e):
    """
    Returns a JSON string with the exception message.
    """
    return json.dumps({"_error": str(e)})


def link_data_row_proxy_to_dict(row):
    d = row_proxy_to_dict(row)
    result = {"object_id": d.pop("object_id"), "object_data": {}}
    for attr in [a for a in d]:
        result["object_data"][attr] = d.pop(attr)
    return result


def markdown_data_row_proxy_to_dict(row):
    d = row_proxy_to_dict(row)
    result = {"object_id": d.pop("object_id"), "object_data": {}}
    for attr in [a for a in d]:
        result["object_data"][attr] = d.pop(attr)
    return result


def deserialize_str_to_datetime(s, allow_none = False, error_msg = None):
    """
    Deserializes ISO-formatted datetime string `s` into datetime object.
    If `allow_none` is set true, treats None as a valid value and returns it.
    Raises `RequestValidationException` in case of failure.
    `error_msg` may be passed to customize error message.
    """
    if allow_none and s is None: return None

    try:
        if s.endswith("Z"): s = s[:-1] # remove Zulu timezone if present to avoid parsing failure
        return datetime.fromisoformat(s)
    except ValueError:
        error_msg = error_msg or f"'{s}' is not a valid ISO-formatted string."
        raise RequestValidationException(error_msg)
