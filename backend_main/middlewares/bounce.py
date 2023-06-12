"""
    Middleware for dispatching additional async tasks.
    Runs searchable data updates whenever original data was modified.
"""
from aiohttp import web

from backend_main.util.json import error_json


@web.middleware
async def bounce_middleware(request, handler):
    """
    Middleware for blocking request processing after app cleanup has started.
    """
    if not request.app["can_process_requests"]["value"]:
        raise web.HTTPServiceUnavailable(text=error_json("Service is unavailable."), content_type="application/json")

    return await handler(request)
