"""
    Auth middleware.
"""
from aiohttp import web

from backend_main.auth.route_access_checks import check_route_access
from backend_main.db_operations.sessions import prolong_access_token_and_get_user_info
from backend_main.util.json import error_json
from backend_main.util.constants import AUTH_SUBAPP_PREFIX

from backend_main.types.request import Request, Handler, UserInfo, request_log_event_key, request_user_info_key


@web.middleware
async def auth_middleware(request: Request, handler: Handler) -> web.Response:
    """
    Checks if requested resource can be accessed by a user with the provided access token.
    """
    # Skip middleware for CORS requests
    if request.method in ("OPTIONS", "HEAD"): return await handler(request)
    
    # Parse access token
    _parse_access_token(request)

    # Validate and prolong token, add user info to the request
    try:
        await prolong_access_token_and_get_user_info(request)
        user_info = request[request_user_info_key]
        user_details = "anonymous" if user_info.is_anonymous else \
            f"user_id = {user_info.user_id}, user_level = {user_info.user_level}"
        request[request_log_event_key]("INFO", "auth", f"Request issued by {user_details}.")
    except web.HTTPUnauthorized:
        request[request_log_event_key]("WARNING", "auth", f"Received invalid access token.")
        raise

    # Check route access
    try:
        check_route_access(request)
    except web.HTTPException:
        request[request_log_event_key]("WARNING", "auth", f"Route access is denied.")
        raise

    # Call next handler
    response = await handler(request)

    # Add new access token expiration time to the response & create web.Response object (except for auth routes)
    if not request.path.startswith(f"/{AUTH_SUBAPP_PREFIX}"):
        # Check if route returned response of a correct type
        if type(response) != dict:
            raise Exception(f"Auth middleware expected {request.path} route handler to return dict, got {type(response)}")
                
        if not user_info.is_anonymous:
            response["auth"] = response.get("auth", {})
            response["auth"]["access_token_expiration_time"] = user_info.access_token_expiration_time.isoformat()
        
        # Create a Response object
        response = web.json_response(response)
    
    return response


def _parse_access_token(request: Request):
    """
    Parses a bearer token from `request` header is it was provided. Adds `user_info` attribute to the `request` object.
    Raises 401 exception if token was provided in an incorrect format.
    """
    access_token = request.headers.get("Authorization")
    
    if access_token is None:
        request[request_user_info_key] = UserInfo()
    else:
        if access_token.find("Bearer ") == 0 and len(access_token) > 7:
            request[request_user_info_key] = UserInfo(access_token[7:])
        else:
            request[request_log_event_key]("WARNING", "auth", f"Invalid Authorization header.")
            raise web.HTTPUnauthorized(text=error_json("Incorrect token format."), content_type="application/json")
