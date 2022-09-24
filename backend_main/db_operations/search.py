from aiohttp import web
from sqlalchemy import select, func, text
from sqlalchemy.sql import and_, or_

from backend_main.db_operations.auth import get_objects_auth_filter_clause, get_tags_auth_filter_clause

from backend_main.util.json import error_json


async def search_items(request, query):
    """
    Searches for searchable items, which match the provided query and sorts them by relevance.
    Returns:
    - list of searchable item IDs which match the query and their type (tag/object);
    - provided `query` parameters;
    - total number of matching items.
    
    Raises a 404 error if no items match the query.
    """
    searchables = request.config_dict["tables"]["searchables"]
    objects = request.config_dict["tables"]["objects"]
    tags = request.config_dict["tables"]["tags"]
    query_text = query["query_text"]
    items_per_page = query["items_per_page"]
    offset = (query["page"] - 1) * items_per_page

    # Objects auth filter for non-admin user levels (applied for objects only)
    objects_auth_filter_clause = or_(searchables.c.object_id == None, 
        get_objects_auth_filter_clause(request, object_ids_subquery=(
            select([searchables.c.object_id])
            .where(and_(
                searchables.c.searchable_tsv_russian.op("@@")(func.websearch_to_tsquery("russian", query_text)),
                searchables.c.object_id != None
            ))
        ))
    )

    # Tags auth filter for non-admin user levels (applied for tags only)
    tags_auth_filter_clause = or_(searchables.c.tag_id == None, 
        get_tags_auth_filter_clause(request, is_published=True)
    )

    # Query database
    result = await request["conn"].execute(
        select([searchables.c.tag_id, searchables.c.object_id,
            # set bit flags for ts_rank function to normalize ranks (2 divides the rank by the document length; 32 divides the rank by itself + 1)
            func.ts_rank(searchables.c.searchable_tsv_russian, func.websearch_to_tsquery("russian", query_text), 2|32).label("rank")]
        )
        .select_from(
            searchables
            .outerjoin(objects, searchables.c.object_id == objects.c.object_id)
            .outerjoin(tags, searchables.c.tag_id == tags.c.tag_id)
        )
        .where(and_(
            objects_auth_filter_clause,
            tags_auth_filter_clause,
            searchables.c.searchable_tsv_russian.op("@@")(func.websearch_to_tsquery("russian", query_text))
        ))
        .order_by(text("rank DESC"))
        .limit(items_per_page)
        .offset(offset)   
    )

    items = [{
        "item_id": row["tag_id"] if row["tag_id"] is not None else row["object_id"],
        "item_type": "tag" if row["tag_id"] is not None else "object"
    } for row in await result.fetchall()]

    # Handle 404 case
    if len(items) == 0: 
        msg = "Nothing was found."
        request.log_event("WARNING", "db_operation", msg)
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")

    # Query total number of items
    result = await request["conn"].execute(
        select([func.count()])
        .select_from(
            searchables
            .outerjoin(objects, searchables.c.object_id == objects.c.object_id)
            .outerjoin(tags, searchables.c.tag_id == tags.c.tag_id)
        )
        .where(and_(
            objects_auth_filter_clause,
            tags_auth_filter_clause,
            searchables.c.searchable_tsv_russian.op("@@")(func.websearch_to_tsquery("russian", query_text))
        ))
    )
    
    total_items = (await result.fetchone())[0]

    # Preparse and rerutn response
    return {
        "query_text": query_text,
        "page": query["page"],
        "items_per_page": query["items_per_page"],
        "items": items,
        "total_items": total_items
    }


# async def search_items(request, query):       # TODO delete after new version is tested
#     """
#     Searches for searchable items, which match the provided query and sorts them by relevance.
#     Returns:
#     - list of searchable item IDs which match the query and their type (tag/object);
#     - provided `query` parameters;
#     - total number of matching items.
    
#     Raises a 404 error if no items match the query.
#     """
#     searchables = request.config_dict["tables"]["searchables"]
#     objects = request.config_dict["tables"]["objects"]
#     query_text = query["query_text"]
#     items_per_page = query["items_per_page"]
#     offset = (query["page"] - 1) * items_per_page

#     # Auth filter for non 'admin` user level
#     auth_filter_clause = or_(get_objects_auth_filter_clause(request), searchables.c.tag_id != None)

#     # Query database
#     result = await request["conn"].execute(
#         select([searchables.c.tag_id, searchables.c.object_id, \
#             # set bit flags for ts_rank function to normalize ranks (2 divides the rank by the document length; 32 divides the rank by itself + 1)
#             func.ts_rank(searchables.c.searchable_tsv_russian, func.websearch_to_tsquery("russian", query_text), 2|32).label("rank")]) \
#         .select_from(searchables.outerjoin(objects, searchables.c.object_id == objects.c.object_id)) \
#         .where(and_(
#             auth_filter_clause,
#             searchables.c.searchable_tsv_russian.op("@@")(func.websearch_to_tsquery("russian", query_text))
#         )) \
#         .order_by(text("rank DESC")) \
#         .limit(items_per_page) \
#         .offset(offset)   
#     )

#     items = [{
#         "item_id": row["tag_id"] if row["tag_id"] is not None else row["object_id"],
#         "item_type": "tag" if row["tag_id"] is not None else "object"
#     } for row in await result.fetchall()]

#     # Handle 404 case
#     if len(items) == 0: 
#         msg = "Nothing was found."
#         request.log_event("WARNING", "db_operation", msg)
#         raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")

#     # Query total number of items
#     result = await request["conn"].execute(
#         select([func.count()])
#         .select_from(searchables.outerjoin(objects, searchables.c.object_id == objects.c.object_id))
#         .where(and_(
#             auth_filter_clause,
#             searchables.c.searchable_tsv_russian.op("@@")(func.websearch_to_tsquery("russian", query_text))
#         ))
#     )
    
#     total_items = (await result.fetchone())[0]

#     # Preparse and rerutn response
#     return {
#         "query_text": query_text,
#         "page": query["page"],
#         "items_per_page": query["items_per_page"],
#         "items": items,
#         "total_items": total_items
#     }
