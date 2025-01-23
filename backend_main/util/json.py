"""
Data converting functions for preparing JSON responses.
"""
from datetime import datetime
import json

from typing import Any
from aiopg.sa.result import RowProxy
from backend_main.types._jsonschema.util import RequestValidationException


def row_proxy_to_dict(row_proxy: RowProxy) -> dict[Any, Any]:
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


def error_json(e: str | Exception) -> str:
    """
    Returns a JSON string with the exception message.
    """
    return json.dumps({"_error": str(e)})


def deserialize_str_to_datetime(
        s: str,
        allow_none: bool = False,
        error_msg: str | None = None
    ):
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
