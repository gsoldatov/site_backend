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
            result[k] = serialize_datetime_to_str(row_proxy[k])
        else:
            result[k] = row_proxy[k]
    return result


def error_json(e):
    """
    Returns a JSON string with the exception message.
    """
    msg = str(e)
    # if isinstance(e, Exception):
    #     msg = e.message
    return json.dumps({"_error": msg})


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


def serialize_datetime_to_str(d):
    # Add UTC timezone and serialize into string
    date_with_timezone = d.replace(tzinfo=timezone.utc)
    return date_with_timezone.isoformat()

