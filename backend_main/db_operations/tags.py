"""
    Common operations with objects_tags table.
"""
from aiohttp import web
from sqlalchemy import select, func
from sqlalchemy.sql import and_

from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_tags


async def add_tag(request, tag_attributes):
    """
        Insert a new row into "tags" table with provided object_attributes.
        Returns a RowProxy object with the inserted data.
    """
    tags = request.config_dict["tables"]["tags"]

    result = await request["conn"].execute(
        tags.insert()
        .returning(tags.c.tag_id, tags.c.created_at, tags.c.modified_at,
                tags.c.tag_name, tags.c.tag_description)
        .values(tag_attributes)
    )

    record = await result.fetchone()

    # Add tag as pending for `searchables` update
    add_searchable_updates_for_tags(request, [record["tag_id"]])
     
    return record 


async def update_tag(request, tag_attributes):
    """
        Updates the tag attributes with provided tag_attributes.
        Returns a RowProxy object with the inserted data.
        Raises a 404 error if tag does not exist.
    """
    tags = request.config_dict["tables"]["tags"]
    tag_id = tag_attributes["tag_id"]

    result = await request["conn"].execute(
        tags.update()
        .where(tags.c.tag_id == tag_id)
        .values(tag_attributes)
        .returning(tags.c.tag_id, tags.c.created_at, tags.c.modified_at,
                tags.c.tag_name, tags.c.tag_description)
    )
    
    record = await result.fetchone()
    if not record:
        raise web.HTTPNotFound(text=error_json(f"tag_id '{tag_id}' not found."), content_type="application/json")
    
    # Add tag as pending for `searchables` update
    add_searchable_updates_for_tags(request, [record["tag_id"]])

    return record


async def view_tags(request, tag_ids):
    """
        Returns a collection of RowProxy objects with tag attributes for provided tag_ids.
        Raises a 404 error tags do not exist.
    """
    tags = request.config_dict["tables"]["tags"]

    rows = await request["conn"].execute(
        select([tags])
        .where(tags.c.tag_id.in_(tag_ids))
    )

    result = await rows.fetchall()
    if len(result) == 0:
        raise web.HTTPNotFound(text=error_json("Requested tags not found."), content_type="application/json")
    
    return result


async def delete_tags(request, tag_ids):
    """
        Deletes tag attributes for provided tag_ids.
        Raises a 404 error if tags do not exist.
    """
    tags = request.config_dict["tables"]["tags"]
    result = await request["conn"].execute(
        tags.delete()
        .where(tags.c.tag_id.in_(tag_ids))
        .returning(tags.c.tag_id)
    )

    if not await result.fetchone():
        raise web.HTTPNotFound(text=error_json("Tag(s) not found."), content_type="application/json")


async def get_page_tag_ids_data(request, pagination_info):
    """
        Get IDs of tags which correspond to the provided pagination_info
        and a total number of matching tags.
        Returns a dict object to be used as a response body.
        Raises a 404 error if no tags match the pagination info.
    """
    # Set query params
    tags = request.config_dict["tables"]["tags"]
    order_by = tags.c.modified_at if pagination_info["order_by"] == "modified_at" else tags.c.tag_name
    order_asc = pagination_info["sort_order"] == "asc"
    items_per_page = pagination_info["items_per_page"]
    first = (pagination_info["page"] - 1) * items_per_page
    filter_text = f"%{pagination_info['filter_text'].lower()}%"

    # return where clause statements for a select statement `s`.
    def with_where_clause(s):
        return s\
            .where(func.lower(tags.c.tag_name).like(filter_text))

    # Get tag ids
    result = await request["conn"].execute(
        with_where_clause(
            select([tags.c.tag_id])
        )
        .order_by(order_by if order_asc else order_by.desc())
        .limit(items_per_page)
        .offset(first)
    )
    tag_ids = []
    for row in await result.fetchall():
        tag_ids.append(row["tag_id"])
    
    if len(tag_ids) == 0:
        raise web.HTTPNotFound(text=error_json("No tags found."), content_type="application/json")

    # Get tag count
    result = await request["conn"].execute(
        with_where_clause(
            select([func.count()])
            .select_from(tags)
        )
    )
    total_items = (await result.fetchone())[0]

    return {
        "page": pagination_info["page"],
        "items_per_page": items_per_page,
        "total_items": total_items,
        "order_by": pagination_info["order_by"],
        "sort_order": pagination_info["sort_order"],
        "filter_text": pagination_info["filter_text"],
        "tag_ids": tag_ids
    }


async def search_tags(request, query):
    """
        Returns a list of tag IDs matching the provided query.
        Raises a 404 error if no tags match the query.
    """
    # Set query params
    tags = request.config_dict["tables"]["tags"]
    query_text = "%" + query["query_text"] + "%"
    maximum_values = query.get("maximum_values", 10)
    existing_ids = query.get("existing_ids", [])

    # Get tag ids
    result = await request["conn"].execute(
        select([tags.c.tag_id])
        .where(and_(
            func.lower(tags.c.tag_name).like(func.lower(query_text)),
            tags.c.tag_id.notin_(existing_ids)
        ))
        .limit(maximum_values)
    )
    tag_ids = []
    for row in await result.fetchall():
        tag_ids.append(row["tag_id"])
    
    if len(tag_ids) == 0:
        raise web.HTTPNotFound(text=error_json("No tags found."), content_type="application/json")
    return tag_ids
