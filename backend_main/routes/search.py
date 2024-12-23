"""
    Search routes.
"""
from aiohttp import web
from jsonschema import validate

from backend_main.db_operations.search import search_items
from backend_main.validation.schemas.search import search_schema

from backend_main.types.request import request_log_event_key


async def search(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=search_schema)

    # Query search results
    result = await search_items(request, data["query"])
    request[request_log_event_key]("INFO", "route_handler", "Returning search results.")
    return result


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("", search, name="search")
                ])
    return app
