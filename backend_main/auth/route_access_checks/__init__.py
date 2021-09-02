"""
Auth middleware checks for specific app routes.
"""
from aiohttp import web


def check_route_access(request):
    """
    Checks if the requested route can be accessed with provided access token.
    """
    # TODO replace with route-specific checks
    if request.user_info.is_anonymous:
        raise web.HTTPUnauthorized(text=error_json("Login required."), content_type="application/json")
    if request.user_info.user_level !== "admin":
        raise web.HTTPForbidden(text=error_json("Access forbidden."), content_type="application/json")