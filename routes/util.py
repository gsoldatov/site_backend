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
