from aiohttp import web
from sqlalchemy import select, func
from sqlalchemy.sql import and_, or_

from backend_main.db_operations.auth import get_objects_auth_filter_clause

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
    query_text = query["query_text"]
    items_per_page = query["items_per_page"]
    offset = (query["page"] - 1) * items_per_page

    # Auth filter for non 'admin` user level
    auth_filter_clause = or_(get_objects_auth_filter_clause(request), searchables.c.tag_id != None)

    # Query database
    result = await request["conn"].execute(
        select([searchables.c.tag_id, searchables.c.object_id, \
            # set bit flags for ts_rank function to normalize ranks (2 divides the rank by the document length; 32 divides the rank by itself + 1)
            func.ts_rank(searchables.c.searchable_tsv_russian, func.websearch_to_tsquery("russian", query_text), 2|32).label("rank")])
        .where(and_(
            auth_filter_clause,
            searchables.c.searchable_tsv_russian.op("@@")(func.websearch_to_tsquery("russian", query_text))
        ))
        .order_by("rank DESC")
        .limit(items_per_page)
        .offset(offset)
    )

    items = [{
        "item_id": row["tag_id"] if row["tag_id"] is not None else row["object_id"],
        "item_type": "tag" if row["tag_id"] is not None else "object"
    } for row in await result.fetchall()]

    # Handle 404 case
    if len(items) == 0: raise web.HTTPNotFound(text=error_json("No results found."), content_type="application/json")

    # Preparse and rerutn response
    return {
        "query_text": query_text,
        "page": query["page"],
        "items_per_page": query["items_per_page"],
        "items": items
    }
