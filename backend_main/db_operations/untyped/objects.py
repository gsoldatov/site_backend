"""
Common operations with objects table.
"""
from aiohttp import web

from backend_main.auth.route_access.common import forbid_non_admin_changing_object_owner
from backend_main.auth.route_checks.objects import authorize_objects_modification
from backend_main.domains.users import ensure_user_ids_exist

from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_objects

from backend_main.types.app import app_tables_key
from backend_main.types.request import request_log_event_key, request_connection_key


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
            request[request_log_event_key]("WARNING", "db_operation", msg, details={"object_id": object_id})
            raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")
        records.append(record)
    
    # Add objects as pending for `searchables` update
    add_searchable_updates_for_objects(request, [o["object_id"] for o in records])
    
    return records


async def add_objects_data(request, object_type, obj_ids_and_data):
    """ 
    Resolves the db operation which adds object data from `obj_ids_and_data` list 
    based on its `object_type`, and calls it.
    """
    if object_type == "link":
        await add_links(request, obj_ids_and_data)
    elif object_type == "markdown":
        await add_markdown(request, obj_ids_and_data)
    elif object_type == "to_do_list":
        await add_to_do_lists(request, obj_ids_and_data)
    elif object_type == "composite":
        return await add_composite(request, obj_ids_and_data)
    else:
        raise NotImplementedError(f"Could not resolve add operation for object type '{object_type}'.")


async def update_objects_data(request, object_type, obj_ids_and_data):
    """ 
    Resolves the db operation which updates object data from `obj_ids_and_data` list 
    based on its `object_type`, and calls it.
    """
    if object_type == "link":
        await update_links(request, obj_ids_and_data)
    elif object_type == "markdown":
        await update_markdown(request, obj_ids_and_data)
    elif object_type == "to_do_list":
        await update_to_do_lists(request, obj_ids_and_data)
    elif object_type == "composite":
        return await update_composite(request, obj_ids_and_data)
    else:
        raise NotImplementedError(f"Could not resolve update operation for object type '{object_type}'.")


# Imports at the bottom of the file to avoid circular references
from backend_main.db_operations.untyped.objects_links import add_links, update_links
from backend_main.db_operations.untyped.objects_markdown import add_markdown, update_markdown
from backend_main.db_operations.untyped.objects_to_do_lists import add_to_do_lists, update_to_do_lists
from backend_main.db_operations.untyped.objects_composite import add_composite, update_composite
