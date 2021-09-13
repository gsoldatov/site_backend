"""
Common operations with objects table.
"""
from datetime import datetime

from aiohttp import web
from sqlalchemy import select, func
from sqlalchemy.sql import and_, or_

from backend_main.auth.route_access_checks.util import debounce_non_admin_changing_object_owner
from backend_main.db_operations.auth import check_if_user_owns_objects, get_objects_auth_filter_clause
from backend_main.db_operations.users import check_if_user_ids_exist

from backend_main.schemas.objects import object_types_enum
from backend_main.util.json import error_json


async def add_objects(request, objects_attributes):
    """
    Insert new rows into "objects" table with provided `objects_attributes` list of attributes values.
    Returns a list of RowProxy objects with the inserted data.
    """
    # Forbid to change object owner for non-admins
    debounce_non_admin_changing_object_owner(request, objects_attributes)
    for o in objects_attributes:
        o.pop("owner_id_is_autoset", None)
    
    # Check if assigned object owners exist
    user_ids = list({o["owner_id"] for o in objects_attributes})
    await check_if_user_ids_exist(request, user_ids)

    # Insert and return new objects
    objects = request.config_dict["tables"]["objects"]

    result = await request["conn"].execute(
        objects.insert()
        .returning(objects.c.object_id, objects.c.object_type, objects.c.created_at, objects.c.modified_at,
                objects.c.object_name, objects.c.object_description, objects.c.is_published, objects.c.owner_id)
        .values(objects_attributes)
        )

    return list(await result.fetchall())


async def update_objects(request, objects_attributes):
    """
    Updates the objects attributes with provided `objects_attributes` list of attribute values.
    Returns a list of RowProxy objects with the inserted data.
    Raises a 400 error if at least one object does not exist.
    """
    # Forbid to change object owner for non-admins
    debounce_non_admin_changing_object_owner(request, objects_attributes, is_objects_update=True)
    for o in objects_attributes:
        o.pop("owner_id_is_autoset", None)
    
    # Check if assigned object owners exist
    user_ids = list({o["owner_id"] for o in objects_attributes if "owner_id" in o})
    await check_if_user_ids_exist(request, user_ids)

    # Check if user can update objects
    object_ids = [o["object_id"] for o in objects_attributes]
    await check_if_user_owns_objects(request, object_ids)

    objects = request.config_dict["tables"]["objects"]
    records = []

    for oa in objects_attributes:
        object_id = oa["object_id"]
    
        result = await request["conn"].execute(
            objects.update()
            .where(objects.c.object_id == object_id)
            .values(oa)
            .returning(objects.c.object_id, objects.c.object_type, objects.c.created_at, objects.c.modified_at,
                    objects.c.object_name, objects.c.object_description, objects.c.is_published, objects.c.owner_id)
            )
        record = await result.fetchone()

        if not record:
            raise web.HTTPBadRequest(text=error_json(f"Failed to update object with object_id '{object_id}': object_id does not exist."), content_type="application/json")
        records.append(record)
    
    return records


async def view_objects(request, object_ids):
    """
    Returns a collection of RowProxy objects with object attributes for provided object_ids.
    """
    objects = request.config_dict["tables"]["objects"]

    # Objects filter for non 'admin` user level
    auth_filter_clause = get_objects_auth_filter_clause(request)

    result = await request["conn"].execute(
        select([objects.c.object_id, objects.c.object_type, objects.c.created_at,
            objects.c.modified_at, objects.c.object_name, objects.c.object_description,
            objects.c.is_published, objects.c.owner_id])
        .where(and_(
            auth_filter_clause,
            objects.c.object_id.in_(object_ids)
        ))
    )
    return await result.fetchall()


async def view_objects_types(request, object_ids):
    """
    Returns a list of object types for the provided object_ids.
    """
    # Objects filter for non 'admin` user level
    auth_filter_clause = get_objects_auth_filter_clause(request)

    objects = request.config_dict["tables"]["objects"]
    result = await request["conn"].execute(
        select([objects.c.object_type])
        .distinct()
        .where(and_(
            auth_filter_clause,
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
    objects = request.config_dict["tables"]["objects"]
    composite = request.config_dict["tables"]["composite"]

    # Get IDs of subobjects which should be deleted (not present in any non-deleted composite objects)
    subobject_ids_to_delete = []
    if delete_subobjects:
        # Get all subobject IDs of deleted subobjects
        result = await request["conn"].execute(
            select([composite.c.subobject_id])
            .distinct()
            .where(composite.c.object_id.in_(object_ids))
        )
        subobjects_of_deleted_objects = set((row["subobject_id"] for row in await result.fetchall()))

        # Get subobject IDs which are present in other composite objects
        result = await request["conn"].execute(
            select([composite.c.subobject_id])
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
    await check_if_user_owns_objects(request, object_and_subobject_ids)

    # Run delete query & return result
    result = await request["conn"].execute(
        objects.delete()
        .where(objects.c.object_id.in_(object_and_subobject_ids))
        .returning(objects.c.object_id)
    )

    if not await result.fetchone():
        raise web.HTTPNotFound(text = error_json("Objects(s) not found."), content_type = "application/json")


async def get_page_object_ids_data(request, pagination_info):
    """
    Get IDs of objects which correspond to the provided pagination_info
    and a total number of matching objects.
    Returns a dict object to be used as a response body.
    Raises a 404 error if no objects match the pagination info.
    """
    objects = request.config_dict["tables"]["objects"]
    objects_tags = request.config_dict["tables"]["objects_tags"]

    # Objects filter for non 'admin` user level
    auth_filter_clause = get_objects_auth_filter_clause(request)

    # Set query params
    order_by = objects.c.modified_at if pagination_info["order_by"] == "modified_at" else objects.c.object_name
    order_asc = pagination_info["sort_order"] == "asc"
    items_per_page = pagination_info["items_per_page"]
    first = (pagination_info["page"] - 1) * items_per_page
    filter_text = f"%{pagination_info['filter_text'].lower()}%"
    object_types = pagination_info["object_types"] if len(pagination_info["object_types"]) > 0 else object_types_enum
    tags_filter = pagination_info["tags_filter"]

    # Sub-query for filtering objects which match tags filter condition
    tags_filter_subquery = (
        select([objects_tags.c.object_id.label("object_id"), func.count().label("tags_count")])
        .where(objects_tags.c.tag_id.in_(tags_filter))
        .group_by(objects_tags.c.object_id)
    ).alias("t_f_subquery")
    tags_filter_query = (
        select([tags_filter_subquery.c.object_id])
        .select_from(tags_filter_subquery)
        .where(tags_filter_subquery.c.tags_count == len(tags_filter))
    ).as_scalar()

    # return where clause statements for a select statement `s`.
    def with_where_clause(s):
        return s\
            .where(auth_filter_clause)\
            .where(func.lower(objects.c.object_name).like(filter_text))\
            .where(objects.c.object_type.in_(object_types))\
            .where(objects.c.object_id.in_(tags_filter_query) if len(tags_filter) > 0 else 1 == 1)

    # Get object ids
    result = await request["conn"].execute(
        with_where_clause(
            select([objects.c.object_id])
        )
        .order_by(order_by if order_asc else order_by.desc())
        .limit(items_per_page)
        .offset(first)
    )
    object_ids = []
    for row in await result.fetchall():
        object_ids.append(row["object_id"])
    
    if len(object_ids) == 0:
        raise web.HTTPNotFound(text = error_json("No objects found."), content_type = "application/json")

    # Get object count
    result = await request["conn"].execute(
        with_where_clause(
            select([func.count()])
            .select_from(objects)
        )
    )
    total_items = (await result.fetchone())[0]

    # Return response
    return {
        "page": pagination_info["page"],
        "items_per_page": items_per_page,
        "total_items": total_items,
        "order_by": pagination_info["order_by"],
        "sort_order": pagination_info["sort_order"],
        "filter_text": pagination_info["filter_text"],
        "object_types": object_types,
        "object_ids": object_ids
    }


async def search_objects(request, query):
    """
    Returns a list of object IDs matching the provided query.
    Raises a 404 error if no objects match the query.
    """
    objects = request.config_dict["tables"]["objects"]
    query_text = "%" + query["query_text"] + "%"
    maximum_values = query.get("maximum_values", 10)
    existing_ids = query.get("existing_ids", [])

    # Objects filter for non 'admin` user level
    auth_filter_clause = get_objects_auth_filter_clause(request)

    # Get object ids
    result = await request["conn"].execute(
        select([objects.c.object_id])
        .where(and_(
            auth_filter_clause,
            func.lower(objects.c.object_name).like(func.lower(query_text)),
            objects.c.object_id.notin_(existing_ids)
        ))
        .limit(maximum_values)
    )
    object_ids = []
    for row in await result.fetchall():
        object_ids.append(row["object_id"])
    
    if len(object_ids) == 0:
        raise web.HTTPNotFound(text = error_json("No objects found."), content_type = "application/json")
    return object_ids


async def set_modified_at(request, object_ids, modified_at = None):
    """
    Updates modified_at attribute for the objects with provided object_ids.
    Returns the updated modified_at value.
    """
    # Check parameter values
    object_ids = object_ids or None
    if type(object_ids) != list:
        raise TypeError("object_ids is not a list or an empty list")

    modified_at = modified_at or datetime.utcnow()
    if type(modified_at) != datetime:
        raise TypeError("modified_at is not a datetime object")

    # Update modified_at
    objects = request.config_dict["tables"]["objects"]
    await request["conn"].execute(objects.update()
        .where(objects.c.object_id.in_(object_ids))
        .values(modified_at = modified_at)
    )
    return modified_at
