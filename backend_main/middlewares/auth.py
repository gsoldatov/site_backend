"""
    Auth middleware.
"""
from aiohttp import web
from datetime import datetime
from pydantic import BaseModel
from typing import cast

from backend_main.auth.route_access import authorize_route_access
from backend_main.domains.sessions import prolong_access_token_and_get_user_info
from backend_main.util.json import error_json
from backend_main.util.constants import AUTH_SUBAPP_PREFIX, ROUTES_ACCESSIBLE_WITH_INVALID_ACCESS_TOKEN

from backend_main.types.request import Request, Handler, UserInfo, request_log_event_key, request_user_info_key


@web.middleware
async def auth_middleware(request: Request, handler: Handler) -> web.Response:
    """
    Checks if requested resource can be accessed by a user with the provided access token.
    """
    # Skip middleware for CORS requests
    if request.method in ("OPTIONS", "HEAD"): return await handler(request)
    
    # Get parsed access token
    access_token = _get_access_token(request)

    # Prolong access token and get user info
    user_info = await prolong_access_token_and_get_user_info(request, access_token)

    # Raise 401 if token was not found or expired, os user is not allowed to login
    if user_info is None:
        request[request_user_info_key] = user_info = UserInfo(access_token=access_token)  # add a stub user info
        request[request_log_event_key]("WARNING", "auth", f"Received invalid access token.")
        
        # Allow invalid tokens for some routes
        if request.path not in ROUTES_ACCESSIBLE_WITH_INVALID_ACCESS_TOKEN:
            raise web.HTTPUnauthorized(text=error_json("Invalid token."), content_type="application/json")
    else:
        request[request_user_info_key] = user_info
        user_details = "anonymous" if user_info.is_anonymous else \
            f"user_id = {user_info.user_id}, user_level = {user_info.user_level}"
        request[request_log_event_key]("INFO", "auth", f"Request issued by {user_details}.")

    # Check route access
    try:
        authorize_route_access(request)
    except web.HTTPException:
        request[request_log_event_key]("WARNING", "auth", f"Route access is denied.")
        raise

    # Call next handler
    response = await handler(request)

    # Add new access token expiration time to the response & create web.Response object (except for auth routes)
    if not request.path.startswith(f"/{AUTH_SUBAPP_PREFIX}"):
        # Convert response to dict
        if isinstance(response, BaseModel): response_dict = response.model_dump()
        elif isinstance(response, dict): response_dict = response
        elif response is None: response_dict = {}
        else: raise Exception(f"Auth middleware expected {request.path} route handler"
                              f" to return dict or pydantic model, got {type(response)}")
                
        if not user_info.is_anonymous:
            response_dict["auth"] = response_dict.get("auth", {})
            access_token_expiration_time = cast(datetime, user_info.access_token_expiration_time)
            response_dict["auth"]["access_token_expiration_time"] = access_token_expiration_time.isoformat()
        
        # Create a Response object
        response = web.json_response(response_dict)
    
    return response


def _get_access_token(request: Request) -> str | None:
    """
    Returns an access token from the "Authorization" header or `None`, if it was not provided.
    Raises 401 exception if the token was provided in an incorrect format.
    """
    access_token = request.headers.get("Authorization")
    
    if access_token is None:
        return None
    else:
        if access_token.find("Bearer ") == 0 and len(access_token) > 7:
            return access_token[7:]
        else:
            request[request_log_event_key]("WARNING", "auth", f"Invalid Authorization header.")
            raise web.HTTPUnauthorized(text=error_json("Incorrect token format."), content_type="application/json")
