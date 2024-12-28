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
from backend_main.db_operations.users import check_if_user_ids_exist

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
    await check_if_user_ids_exist(request, user_ids)

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
    await check_if_user_ids_exist(request, user_ids)

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


async def view_objects(request, object_ids):
    """
    Returns a collection of RowProxy objects with object attributes for provided object_ids.
    """
    objects = request.config_dict[app_tables_key].objects

    # Objects filter for non 'admin` user level
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

    result = await request[request_connection_key].execute(
        select(objects.c.object_id, objects.c.object_type, objects.c.created_at,
            objects.c.modified_at, objects.c.object_name, objects.c.object_description, objects.c.is_published, 
            objects.c.display_in_feed, objects.c.feed_timestamp, objects.c.show_description, objects.c.owner_id)
        .where(and_(
            objects_auth_filter_clause,
            objects.c.object_id.in_(object_ids)
        ))
    )
    return await result.fetchall()


async def view_objects_types(request, object_ids):
    """
    Returns a list of object types for the provided object_ids.
    """
    objects = request.config_dict[app_tables_key].objects

    # Objects filter for non 'admin` user level
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

    result = await request[request_connection_key].execute(
        select(objects.c.object_type)
        .distinct()
        .where(and_(
            objects_auth_filter_clause,
            objects.c.object_id.in_(object_ids)
        ))
    )

    object_types = []
    for row in await result.fetchall():
        object_types.append(row["object_type"])
    return object_types


async def delete_objects(request, object_ids, delete_subobjects = False):
    """
    Deletes object attributes for provided object_ids.
    """
    objects = request.config_dict[app_tables_key].objects
    composite = request.config_dict[app_tables_key].composite

    # Get IDs of subobjects which should be deleted (not present in any non-deleted composite objects)
    subobject_ids_to_delete = []
    if delete_subobjects:
        # Get all subobject IDs of deleted subobjects
        result = await request[request_connection_key].execute(
            select(composite.c.subobject_id)
            .distinct()
            .where(composite.c.object_id.in_(object_ids))
        )
        subobjects_of_deleted_objects = set((row["subobject_id"] for row in await result.fetchall()))

        # Get subobject IDs which are present in other composite objects
        result = await request[request_connection_key].execute(
            select(composite.c.subobject_id)
            .distinct()
            .where(and_(
                composite.c.subobject_id.in_(subobjects_of_deleted_objects),
                composite.c.object_id.notin_(object_ids)
            ))
        )
        subobjects_present_in_other_objects = set((row["subobject_id"] for row in await result.fetchall()))
        
        # Get subobject IDs which are present only in deleted composite objects
        subobject_ids_to_delete = subobjects_of_deleted_objects.difference(subobjects_present_in_other_objects)
    
    # Check if user can delete objects and subobjects
    object_and_subobject_ids = [o for o in object_ids]
    object_and_subobject_ids.extend(subobject_ids_to_delete)
    await authorize_objects_modification(request, object_and_subobject_ids)

    # Run delete query & return result
    result = await request[request_connection_key].execute(
        objects.delete()
        .where(objects.c.object_id.in_(object_and_subobject_ids))
        .returning(objects.c.object_id)
    )

    if not await result.fetchone():
        msg = "Attempted to delete non-existing object(-s)."
        request[request_log_event_key]("WARNING", "db_operation", msg, details=f"object_ids = {object_ids}")
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")
    
    request[request_log_event_key]("INFO", "db_operation", "Deleted objects.", details=f"object_ids = {object_ids}, subobject_ids = {subobject_ids_to_delete}")


async def get_page_object_ids_data(request, pagination_info):
    """
    Get IDs of objects which correspond to the provided pagination_info
    and a total number of matching objects.
    Returns a dict object to be used as a response body.
    Raises a 404 error if no objects match the pagination info.
    """
    objects = request.config_dict[app_tables_key].objects
    objects_tags = request.config_dict[app_tables_key].objects_tags

    # Basic query parameters and clauses
    order_by = {
        "object_name": objects.c.object_name,
        "modified_at": objects.c.modified_at,
        "feed_timestamp": coalesce(objects.c.feed_timestamp, objects.c.modified_at)
    }[pagination_info["order_by"]]
    order_asc = pagination_info["sort_order"] == "asc"
    items_per_page = pagination_info["items_per_page"]
    first = (pagination_info["page"] - 1) * items_per_page

    # Optional search condidions
    def with_where_clause(s):
        """ Returns where clause statements for a select statement `s`. """
        # Text filter for object name
        filter_text = pagination_info.get("filter_text", "")
        if len(filter_text) > 0: filter_text = f"%{filter_text.lower()}%"
        text_filter_clause = func.lower(objects.c.object_name).like(filter_text) if len(filter_text) > 0 else true()

        # Object types filter
        object_types = pagination_info.get("object_types", [])
        object_types_clause = objects.c.object_type.in_(object_types) if len(object_types) > 0 else true()

        # Tags filter
        tags_filter_clause = true()
        if len(pagination_info.get("tags_filter", [])) > 0:
            tags_filter = pagination_info["tags_filter"]

            # Sub-query for filtering objects which match tags filter condition
            tags_filter_subquery = (
                select(objects_tags.c.object_id.label("object_id"), func.count().label("tags_count"))
                .where(objects_tags.c.tag_id.in_(tags_filter))
                .group_by(objects_tags.c.object_id)
            ).alias("t_f_subquery")
            tags_filter_query = (
                select(tags_filter_subquery.c.object_id)
                .select_from(tags_filter_subquery)
                .where(tags_filter_subquery.c.tags_count == len(tags_filter))
            ).scalar_subquery()

            tags_filter_clause = objects.c.object_id.in_(tags_filter_query)
        
        # Display in feed
        display_in_feed_clause = true()
        if pagination_info.get("show_only_displayed_in_feed"):
            display_in_feed_clause = objects.c.display_in_feed == pagination_info["show_only_displayed_in_feed"]
        
        # Objects filter for non 'admin` user level
        objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids_subquery=(
            select(objects.c.object_id)
            .where(text_filter_clause)
            .where(object_types_clause)
            .where(tags_filter_clause)
            .where(display_in_feed_clause)
        ))
        
        # Resulting statement
        return (
            s
            .where(objects_auth_filter_clause)
            .where(text_filter_clause)
            .where(object_types_clause)
            .where(tags_filter_clause)
            .where(display_in_feed_clause)
        )

    # Get object ids
    result = await request[request_connection_key].execute(
        with_where_clause(
            select(objects.c.object_id)
        )
        .order_by(order_by if order_asc else order_by.desc())
        .limit(items_per_page)
        .offset(first)
    )
    object_ids = []
    for row in await result.fetchall():
        object_ids.append(row["object_id"])
    
    if len(object_ids) == 0:
        msg = "No objects found."
        request[request_log_event_key]("WARNING", "db_operation", msg)
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")

    # Get object count
    result = await request[request_connection_key].execute(
        with_where_clause(
            select(func.count())
            .select_from(objects)
        )
    )
    total_items = (await result.fetchone())[0]

    # Return response
    result = {
        "page": pagination_info["page"],
        "items_per_page": items_per_page,
        "total_items": total_items,
        "order_by": pagination_info["order_by"],
        "sort_order": pagination_info["sort_order"],
        "object_ids": object_ids
    }

    for attr in ("filter_text", "object_types", "tags_filter"):
        if attr in pagination_info: result[attr] = pagination_info[attr]
    return {"pagination_info": result}


async def search_objects(request, query):
    """
    Returns a list of object IDs matching the provided query.
    Raises a 404 error if no objects match the query.
    """
    objects = request.config_dict[app_tables_key].objects
    query_text = "%" + query["query_text"] + "%"
    maximum_values = query.get("maximum_values", 10)
    existing_ids = query.get("existing_ids", [])

    # Objects filter for non 'admin` user level
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids_subquery=(
        select(objects.c.object_id)
        .where(and_(
            func.lower(objects.c.object_name).like(func.lower(query_text)),
            objects.c.object_id.notin_(existing_ids)
        ))
    ))

    # Get object ids
    result = await request[request_connection_key].execute(
        select(objects.c.object_id)
        .where(and_(
            objects_auth_filter_clause,
            func.lower(objects.c.object_name).like(func.lower(query_text)),
            objects.c.object_id.notin_(existing_ids)
        ))
        .limit(maximum_values)
    )
    object_ids = []
    for row in await result.fetchall():
        object_ids.append(row["object_id"])
    
    if len(object_ids) == 0:
        msg = "No objects found."
        request[request_log_event_key]("WARNING", "db_operation", msg)
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")
    return object_ids


async def get_elements_in_composite_hierarchy(request, object_id):
    """
    Returns all object IDs in the composite hierarchy, which starts from `object_id`.
    Maximum depth of hierarchy, which is checked, is limited by `composite_hierarchy_max_depth` configuration setting.

    If `object_id` can't be viewed with the current auth level, raises 404.
    If `object_id` does not belong to a composite object, raises 400.
    """
    objects = request.config_dict[app_tables_key].objects
    composite = request.config_dict[app_tables_key].composite

    # Check if object is composite and can be viewed by request sender
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=[object_id])
    result = await request[request_connection_key].execute(
        select(objects.c.object_type)
        .where(and_(
            objects_auth_filter_clause,
            objects.c.object_id == object_id
        ))
    )

    row = await result.fetchone()
    # Throw 404 if object can't be viewed
    if not row:
        msg = "Object not found."
        request[request_log_event_key]("WARNING", "db_operation", msg, details=f"object_id = {object_id}")
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")

    # Throw 400 if root object is not composite
    if row[0] != "composite":
        msg = "Attempted to loop through a hierarchy of a non-composite object."
        request[request_log_event_key]("WARNING", "db_operation", msg, details=f"object_id = {object_id}")
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")

    # Build a hierarchy
    parent_object_ids = [object_id]
    all_composite, all_non_composite = set([object_id]), set()
    current_depth = 1

    while len(parent_object_ids) > 0 and current_depth < request.config_dict[app_config_key].app.composite_hierarchy_max_depth:
        # Query all subobjects of current parents
        result = await request[request_connection_key].execute(
            select(composite.c.subobject_id, objects.c.object_type)
            .select_from(composite.join(objects, composite.c.subobject_id == objects.c.object_id))
            .where(composite.c.object_id.in_(parent_object_ids))    # Do not apply auth filter here (it will be applied when objects' attributes & data are fetched)
        )

        # Get sets with new composite & non-composite object ids
        new_composite, new_non_composite = set(), set()
        for row in await result.fetchall():
            s = new_composite if row["object_type"] == "composite" else new_non_composite
            s.add(row["subobject_id"])
        
        # Combine new & total sets of object IDs and exit the loop if there is no new composite objects, which were not previously fetched in the loop
        all_non_composite.update(new_non_composite)

        non_fetched_composite = new_composite.difference(all_composite)
        all_composite.update(non_fetched_composite)
        parent_object_ids = non_fetched_composite
        current_depth += 1
    
    return {"composite": list(all_composite), "non_composite": list(all_non_composite)}


async def set_modified_at(request, object_ids, modified_at = None):
    """
    Sets `modified_at` attribute for the objects with provided `object_ids` to provided value or request time.
    Returns the updated `modified_at` value.
    """
    modified_at = modified_at or request[request_time_key]

    # Update modified_at
    objects = request.config_dict[app_tables_key].objects
    await request[request_connection_key].execute(objects.update()
        .where(objects.c.object_id.in_(object_ids))
        .values(modified_at=modified_at)
    )
    return modified_at
