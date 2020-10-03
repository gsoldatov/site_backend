"""
Utility functions.
"""
from datetime import datetime
from urllib.parse import urlparse
import json


def row_proxy_to_dict(row_proxy):
    """
    Converts SQLAlchemy RowProxy object into a dict.
    datetime fields are converted into strings.
    """
    return {k: row_proxy[k] if type(row_proxy[k]) != datetime else str(row_proxy[k]) for k in row_proxy}


def objects_row_proxy_to_dict(row_proxy):
    """
    Converts row proxy object with object data into into a dict.
    """
    row = row_proxy_to_dict(row_proxy)
    obj_type = row["object_type"]
    if obj_type == "link":
        row["object_data"] = {"link": row["link"]}
    
    for attr in ["link"]:
        row.pop(attr, None)
    
    return row



def error_json(e):
    """
    Returns a JSON string with the exception message.
    """
    msg = e
    if isinstance(e, Exception):
        msg = e.message
    return json.dumps({"_error": msg})


def validate_url(url):
    """
    Checks if provided string is a valid URL and raises 
    """
    result = urlparse(url)
    if not result.scheme or not result.netloc:
        raise URLValidationException("Provided string is not a valid URL")


class URLValidationException(Exception):
    def __init__(self, message):
        self.message = message


async def check_if_tag_id_exists(request, tag_id):
    """
    Returns True if tag_id exists in the database of False otherwise.
    """
    async with request.app["engine"].acquire() as conn:
        try:
            tag_id = int(tag_id)
            if tag_id < 1:
                raise ValueError
            
            tags = request.app["tables"]["tags"]
            result = await conn.execute(tags.select().where(tags.c.tag_id == tag_id))
            if not await result.fetchone():
                raise ValueError

            return True
        except ValueError:
            return False
