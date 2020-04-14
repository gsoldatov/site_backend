"""
Utility functions.
"""
from datetime import datetime
import json

def row_proxy_to_dict(row_proxy):
    """
    Converts SQLAlchemy RowProxy object into dict.
    datetime fields are converted into strings.
    """
    return {k: row_proxy[k] if type(row_proxy[k]) != datetime else str(row_proxy[k]) for k in row_proxy}


def error_json(e):
    """
    Returns a JSON string with the exception message.
    """
    msg = e
    if isinstance(e, Exception):
        msg = e.message
    return json.dumps({"_error": msg})