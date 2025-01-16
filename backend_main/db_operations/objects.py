"""
Common operations with objects table.
"""
from aiohttp import web
from sqlalchemy import select, func
from sqlalchemy.sql import and_
from sqlalchemy.sql.expression import true
from sqlalchemy.sql.functions import coalesce

from backend_main.auth.route_access.common import forbid_non_admin_changing_object_owner
from backend_main.auth.route_checks.objects import authorize_objects_modification
from backend_main.auth.query_clauses import get_objects_auth_filter_clause
from backend_main.domains.users import ensure_user_ids_exist

from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_objects

from backend_main.types.app import app_config_key, app_tables_key
from backend_main.types.request import request_time_key, request_log_event_key, request_connection_key


async def add_objects(request, objects_attributes):
    """
    Insert new rows into "objects" table with provided `objects_attributes` list of attributes values.
    Returns a list of RowProxy objects with the inserted data.
    """
    # Forbid to change object owner for non-admins
    forbid_non_admin_changing_object_owner(request, objects_attributes)
    for o in objects_attributes:
        o.pop("owner_id_is_autoset", None)
    
    # Check if assigned object owners exist
    user_ids = list({o["owner_id"] for o in objects_attributes})
    await ensure_user_ids_exist(request, user_ids)

    # Insert new objects
    objects = request.config_dict[app_tables_key].objects

    result = await request[request_connection_key].execute(
        objects.insert()
        .returning(objects.c.object_id, objects.c.object_type, objects.c.created_at, objects.c.modified_at,
                objects.c.object_name, objects.c.object_description, objects.c.is_published, 
                objects.c.display_in_feed, objects.c.feed_timestamp, objects.c.show_description, objects.c.owner_id)
        .values(objects_attributes)
        )
    
    added_object_attributes = list(await result.fetchall())

    # Add objects as pending for `searchables` update
    add_searchable_updates_for_objects(request, [o["object_id"] for o in added_object_attributes])

    return added_object_attributes


async def update_objects(request, objects_attributes):
    """
    Updates the objects attributes with provided `objects_attributes` list of attribute values.
    Returns a list of RowProxy objects with the inserted data.
    Raises a 400 error if at least one object does not exist.
    """
    # Forbid to change object owner for non-admins
    forbid_non_admin_changing_object_owner(request, objects_attributes, is_objects_update=True)
    for o in objects_attributes:
        o.pop("owner_id_is_autoset", None)
    
    # Check if assigned object owners exist
    user_ids = list({o["owner_id"] for o in objects_attributes if "owner_id" in o})
    await ensure_user_ids_exist(request, user_ids)

    # Check if user can update objects
    object_ids = [o["object_id"] for o in objects_attributes]
    await authorize_objects_modification(request, object_ids)

    objects = request.config_dict[app_tables_key].objects
    records = []

    for oa in objects_attributes:
        object_id = oa["object_id"]
    
        result = await request[request_connection_key].execute(
            objects.update()
            .where(objects.c.object_id == object_id)
            .values(oa)
            .returning(objects.c.object_id, objects.c.object_type, objects.c.created_at, objects.c.modified_at,
                    objects.c.object_name, objects.c.object_description, objects.c.is_published, 
                    objects.c.display_in_feed, objects.c.feed_timestamp, objects.c.show_description, objects.c.owner_id)
            )
        record = await result.fetchone()

        if not record:
            msg = "Attempted to update attributes of a non-existing object."
            request[request_log_event_key]("WARNING", "db_operation", msg, details=f"object_id = {object_id}")
            raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")
        records.append(record)
    
    # Add objects as pending for `searchables` update
    add_searchable_updates_for_objects(request, [o["object_id"] for o in records])
    
    return records
