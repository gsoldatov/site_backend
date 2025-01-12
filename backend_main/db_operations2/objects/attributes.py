from sqlalchemy import select, func
from sqlalchemy.sql import and_, true
from sqlalchemy.sql.functions import coalesce

from backend_main.auth.query_clauses import get_objects_auth_filter_clause

from backend_main.util.exceptions import ObjectsNotFound

from datetime import datetime
from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key


async def update_modified_at(request: Request, object_ids: list[int], modified_at: datetime) -> datetime:
    """
    Updates `modified_at` attribute of the objects with provided `object_ids` to the provided value.
    Returns the updated `modified_at` value.
    """
    # Update modified_at
    objects = request.config_dict[app_tables_key].objects
    await request[request_connection_key].execute(objects.update()
        .where(objects.c.object_id.in_(object_ids))
        .values(modified_at=modified_at)
    )
    return modified_at
