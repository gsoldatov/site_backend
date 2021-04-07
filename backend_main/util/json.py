"""
Data converting functions for preparing JSON responses.
"""
from datetime import datetime, timezone
import json


def row_proxy_to_dict(row_proxy):
    """
    Converts SQLAlchemy RowProxy object into a dict.
    datetime fields are converted into strings.
    """
    result = {}
    for k in row_proxy:
        if type(row_proxy[k]) == datetime:
            # Add UTC timezone and serialize into string
            date_with_timezone = row_proxy[k].replace(tzinfo=timezone.utc)
            result[k] = date_with_timezone.isoformat()
        else:
            result[k] = row_proxy[k]
    return result


def error_json(e):
    """
    Returns a JSON string with the exception message.
    """
    msg = e
    if isinstance(e, Exception):
        msg = e.message
    return json.dumps({"_error": msg})


def link_data_row_proxy_to_dict(row):
    result = row_proxy_to_dict(row)
    result["object_data"] = {"link": result.pop("link")}
    return result


def markdown_data_row_proxy_to_dict(row):
    result = row_proxy_to_dict(row)
    result["object_data"] = {"raw_text": result.pop("raw_text")}
    return result
