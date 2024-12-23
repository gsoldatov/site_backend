"""
    Authorization & authentication routes.
"""
from aiohttp import web
from datetime import timedelta
from jsonschema import validate

from backend_main.db_operations.auth import check_if_non_admin_can_register
from backend_main.db_operations.login_rate_limits import add_login_rate_limit_to_request, \
    upsert_login_rate_limit, delete_login_rate_limits
from backend_main.db_operations.sessions import add_session, delete_sessions
from backend_main.db_operations.users import add_user, get_user_by_credentials
from backend_main.middlewares.connection import start_transaction

from backend_main.validation.schemas.auth import register_schema, login_schema

from backend_main.util.constants import forbidden_non_admin_user_modify_attributes
from backend_main.util.json import error_json, row_proxy_to_dict
from backend_main.util.login_rate_limits import get_login_attempts_timeout_in_seconds, IncorrectCredentialsException

from backend_main.types.request import request_time_key, request_log_event_key, request_user_info_key


async def register(request):
    # Debounce anonymous if non-admin registration is disabled
    await check_if_non_admin_can_register(request)

    # Validate request schema
    data = await request.json()
    validate(instance=data, schema=register_schema)

    # Check password
    if data["password"] != data["password_repeat"]:
        msg = "Password is not correctly repeated."
        request[request_log_event_key]("WARNING", "route_handler", msg)
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")

    # Check if non-admins are not trying to set privileges
    if request[request_user_info_key].user_level != "admin":
        for attr in forbidden_non_admin_user_modify_attributes:
            if attr in data:
                msg = "User privileges can only be set by admins."
                request[request_log_event_key]("WARNING", "route_handler", msg)
                raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
    
    # Set default values
    data.pop("password_repeat")
    request_time = request[request_time_key]
    data["registered_at"] = request_time
    if "user_level" not in data: data["user_level"] = "user"
    if "can_login" not in data: data["can_login"] = True
    if "can_edit_objects" not in data: data["can_edit_objects"] = True

    # Add the user
    result = await add_user(request, data)
    user = row_proxy_to_dict(result)
    request[request_log_event_key]("INFO", "route_handler", f"Registered user {user['user_id']}.")

    # Don't send user info if admin token was not provided (registration form processing case)
    if request[request_user_info_key].user_level != "admin": return web.Response()

    # Return new user's data in case of admin registration
    return web.json_response({"user": user})


async def login(request):
    # Check and get login rate limits
    try:
        await add_login_rate_limit_to_request(request)
    except web.HTTPTooManyRequests:
        request[request_log_event_key]("WARNING", "route_handler", "Log in rate limit is exceeded.")
        raise

    # Validate request schema
    data = await request.json()
    validate(instance=data, schema=login_schema)

    # Try to get user data
    user_data = await get_user_by_credentials(request, login=data["login"], password=data["password"])

    # User was not found
    if user_data is None:
        request_time = request[request_time_key]

        # Update login rate limits
        lrli = request["login_rate_limit_info"]
        lrli.cant_login_until = request_time + \
            timedelta(seconds=get_login_attempts_timeout_in_seconds(lrli.failed_login_attempts))
        lrli.failed_login_attempts += 1
        await upsert_login_rate_limit(request, lrli)

        # Raise 401 with committing database changes
        request[request_log_event_key]("WARNING", "route_handler", f"Incorrect user credentials.")
        raise IncorrectCredentialsException()
    
    # User was found
    else:
        # If user can't login, raise 403
        if not user_data.can_login:
            msg = "User is not allowed to login."
            request[request_log_event_key]("WARNING", "route_handler", msg)
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
        
        # Start a transaction
        await start_transaction(request)
        
        # Create a session
        session = await add_session(request, user_data.user_id)

        # Delete login rate limit for the request issuer
        await delete_login_rate_limits(request, [request.remote])

        # Return access token
        request[request_log_event_key]("INFO", "route_handler", f"User {user_data.user_id} logged in.")
        return web.json_response({"auth": {
            "access_token": session["access_token"],
            "access_token_expiration_time": session["expiration_time"].isoformat(),
            "user_id": user_data.user_id,
            "user_level": user_data.user_level
        }})


async def logout(request):
    # Delete session (if it does not exist, return 200 anyway)
    user_info = request[request_user_info_key]
    await delete_sessions(request, access_tokens=[user_info.access_token])
    request[request_log_event_key]("INFO", "route_handler", f"User {user_info.user_id} logged out.")
    return web.Response()


def get_subapp():
    app = web.Application()
    app.add_routes([
        web.post("/register", register, name="register"),
        web.post("/login", login, name="login"),
        web.post("/logout", logout, name="logout")
        ])
    return app
