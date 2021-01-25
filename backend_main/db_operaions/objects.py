"""
    Common operations with objects table.
"""
from datetime import datetime

from aiohttp import web
from sqlalchemy import select, func
from sqlalchemy.sql import and_

from backend_main.schemas.objects import object_types_enum
from backend_main.util.json import error_json


async def add_object(request, object_attributes):
    """
        Insert a new row into "objects" table with provided object_attributes.
        Returns a RowProxy object with the inserted data.
    """
    objects = request.app["tables"]["objects"]

    result = await request["conn"].execute(
        objects.insert()
        .returning(objects.c.object_id, objects.c.object_type, objects.c.created_at, objects.c.modified_at,
                objects.c.object_name, objects.c.object_description)
        .values(object_attributes)
        )
    return await result.fetchone()


async def update_object(request, object_attributes):
    """
        Updates the object attributes with provided object_attributes.
        Returns a RowProxy object with the inserted data.
        Raises a 404 error if object does not exist.
    """
    objects = request.app["tables"]["objects"]
    object_id = object_attributes["object_id"]
    
    result = await request["conn"].execute(
        objects.update()
        .where(objects.c.object_id == object_id)
        .values(object_attributes)
        .returning(objects.c.object_id, objects.c.object_type, objects.c.created_at, objects.c.modified_at,
                objects.c.object_name, objects.c.object_description)
        )
    record = await result.fetchone()
    if not record:
        raise web.HTTPNotFound(text = error_json(f"object_id '{object_id}' not found."), content_type = "application/json")
    return record


async def view_objects(request, object_ids):
    """
        Returns a collection of RowProxy objects with object attributes for provided object_ids.
    """
    objects = request.app["tables"]["objects"]

    result = await request["conn"].execute(
        select([objects.c.object_id, objects.c.object_type, objects.c.created_at,
            objects.c.modified_at, objects.c.object_name, objects.c.object_description])
        .where(objects.c.object_id.in_(object_ids))
    )
    return await result.fetchall()
    


async def view_objects_types(request, object_ids):
    """
        Returns a list of object types for the provided object_ids.
    """
    objects = request.app["tables"]["objects"]
    result = await request["conn"].execute(
        select([objects.c.object_type])
        .distinct()
        .where(objects.c.object_id.in_(object_ids))
    )

    object_types = []
    for row in await result.fetchall():
        object_types.append(row["object_type"])
    return object_types


async def delete_objects(request, object_ids):
    """
        Deletes object attributes for provided object_ids.
    """
    objects = request.app["tables"]["objects"]
    result = await request["conn"].execute(
        objects.delete()
        .where(objects.c.object_id.in_(object_ids))
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
    objects = request.app["tables"]["objects"]
    objects_tags = request.app["tables"]["objects_tags"]

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

    # Get object ids
    result = await request["conn"].execute(
        select([objects.c.object_id])
        .where(func.lower(objects.c.object_name).like(filter_text))
        .where(objects.c.object_type.in_(object_types))
        .where(objects.c.object_id.in_(tags_filter_query) if len(tags_filter) > 0 else 1 == 1)
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
        select([func.count()])
        .select_from(objects)
        .where(objects.c.object_name.like(filter_text))
        .where(objects.c.object_type.in_(object_types))
        .where(objects.c.object_id.in_(tags_filter_query) if len(tags_filter) > 0 else 1 == 1)
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
    objects = request.app["tables"]["objects"]
    query_text = "%" + query["query_text"] + "%"
    maximum_values = query.get("maximum_values", 10)
    existing_ids = query.get("existing_ids", [])

    # Get object ids
    result = await request["conn"].execute(
        select([objects.c.object_id])
        .where(and_(
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
    objects = request.app["tables"]["objects"]
    await request["conn"].execute(objects.update()
        .where(objects.c.object_id.in_(object_ids))
        .values(modified_at = modified_at)
    )
    return modified_at
