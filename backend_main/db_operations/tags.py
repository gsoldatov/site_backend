"""
    Common operations with objects_tags table.
"""
from aiohttp import web
from sqlalchemy import select, func
from sqlalchemy.sql import and_

from backend_main.auth.route_access.common import forbid_non_admin_changing_object_owner

from backend_main.auth.query_clauses import get_tags_auth_filter_clause

from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_tags

from backend_main.types.app import app_tables_key
from backend_main.types.request import request_log_event_key, request_connection_key


async def get_page_tag_ids_data(request, pagination_info):
    """
        Get IDs of tags which correspond to the provided pagination_info
        and a total number of matching tags.
        Returns a dict object to be used as a response body.
        Raises a 404 error if no tags match the pagination info.
    """
    # Set query params
    tags = request.config_dict[app_tables_key].tags
    order_by = tags.c.modified_at if pagination_info["order_by"] == "modified_at" else tags.c.tag_name
    order_asc = pagination_info["sort_order"] == "asc"
    items_per_page = pagination_info["items_per_page"]
    first = (pagination_info["page"] - 1) * items_per_page
    filter_text = f"%{pagination_info['filter_text'].lower()}%"

    # Tags auth filter for non-admin user levels
    tags_auth_filter_clause = get_tags_auth_filter_clause(request, is_published=True)

    # return where clause statements for a select statement `s`.
    def with_where_clause(s):
        return (
            s.where(and_(
                tags_auth_filter_clause,
                func.lower(tags.c.tag_name).like(filter_text)
            ))
        )

    # Get tag ids
    result = await request[request_connection_key].execute(
        with_where_clause(
            select(tags.c.tag_id)
        )
        .order_by(order_by if order_asc else order_by.desc())
        .limit(items_per_page)
        .offset(first)
    )
    tag_ids = []
    for row in await result.fetchall():
        tag_ids.append(row["tag_id"])
    
    if len(tag_ids) == 0:
        msg = "No tags found."
        request[request_log_event_key]("WARNING", "db_operation", msg)
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")

    # Get tag count
    result = await request[request_connection_key].execute(
        with_where_clause(
            select(func.count())
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
    tags = request.config_dict[app_tables_key].tags
    query_text = "%" + query["query_text"] + "%"
    maximum_values = query.get("maximum_values", 10)
    existing_ids = query.get("existing_ids", [])

    # Tags auth filter for non-admin user levels
    tags_auth_filter_clause = get_tags_auth_filter_clause(request, is_published=True)

    # Get tag ids
    result = await request[request_connection_key].execute(
        select(tags.c.tag_id)
        .where(and_(
            tags_auth_filter_clause,
            func.lower(tags.c.tag_name).like(func.lower(query_text)),
            tags.c.tag_id.notin_(existing_ids)
        ))
        .limit(maximum_values)
    )
    tag_ids = []
    for row in await result.fetchall():
        tag_ids.append(row["tag_id"])
    
    if len(tag_ids) == 0:
        msg = "No tags found."
        request[request_log_event_key]("WARNING", "db_operation", msg)
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")
    
    return tag_ids
