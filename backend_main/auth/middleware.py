"""
    Auth middleware.
"""
from aiohttp import web

from backend_main.db_operations.sessions import prolong_access_token_and_get_user_info
from backend_main.auth.route_access_checks import check_route_access
from backend_main.util.json import error_json


@web.middleware
async def auth_middleware(request, handler):
    """
    Checks if requested resource can be accessed by a user with the provided access token
    """
    # Parse access token
    parse_access_token(request)

    # Validate and prolong token, add user info to the request
    await prolong_access_token_and_get_user_info(request)

    # Check route access
    check_route_access(request)

    # Call next handler
    return await handler(request)


def parse_access_token(request):
    """
    Parses a bearer token from `request` header is it was provided. Adds `user_info` attribute to the `request` object.
    Raises 401 exception if token was provided in an incorrect format.
    """
    access_token = request.headers.get("Authorization")
    
    if access_token is None:
        request.user_info = UserInfo()
    else:
        if access_token.find("Bearer ") == 0:
            request.user_info = UserInfo(access_token[7:])
        else:
            raise web.HTTPUnauthorized(text=error_json("Incorrect token format."), content_type="application/json")


class UserInfo:
    """
    Dataclass for storing user information which corresponds to the provided `token`.
    """
    __slots__ = ["access_token", "is_anonymous", "user_id", "user_level", "can_edit_objects"]

    def __init__(self, access_token = None):
        self.access_token = access_token
        self.is_anonymous = access_token is None
        
        self.user_id = None
        self.user_level = None
        self.can_edit_objects = None
