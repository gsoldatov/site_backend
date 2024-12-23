"""
    Middleware for dispatching additional async tasks.
    Runs searchable data updates whenever original data was modified.
"""
from aiohttp import web

from backend_main.util.json import error_json

from backend_main.types.app import app_can_process_requests_key


@web.middleware
async def bounce_middleware(request, handler):
    """
    Middleware for blocking request processing after app cleanup has started.
    """
    if not request.config_dict[app_can_process_requests_key]["value"]:
        raise web.HTTPServiceUnavailable(text=error_json("Service is unavailable."), content_type="application/json")

    return await handler(request)
