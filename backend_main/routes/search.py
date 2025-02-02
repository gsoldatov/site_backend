"""
    Search route handlers.
"""
from aiohttp import web

from backend_main.domains.search import get_search_results

from backend_main.util.json import error_json

from backend_main.types.request import Request, request_log_event_key
from backend_main.types.routes.search import SearchRequestBody, SearchResponseBody


async def search(request: Request) -> SearchResponseBody:
    # Validate request body
    data = SearchRequestBody.model_validate(await request.json())    

    # Query search results
    search_results = await get_search_results(request, data.query)

    if len(search_results.items) == 0: 
        msg = "Nothing was found."
        request[request_log_event_key]("WARNING", "route_handler", msg)
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")

    request[request_log_event_key]("INFO", "route_handler", "Returning search results.")
    return SearchResponseBody.model_validate(search_results, from_attributes=True)


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("", search, name="search")
                ])
    return app
