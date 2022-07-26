"""
    Search routes.
"""
from aiohttp import web
from jsonschema import validate

from backend_main.db_operations.search import search_items
from backend_main.validation.schemas.search import search_schema


async def search(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=search_schema)

    # Query search results
    result = await search_items(request, data["query"])
    request.log_event("INFO", "route_handler", "Returning search results.")
    return result


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("", search, name="search")
                ])
    return app
