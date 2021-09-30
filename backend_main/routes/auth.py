"""
    Authorization & authentication routes.
"""
from aiohttp import web
from datetime import datetime, timedelta
from jsonschema import validate

from backend_main.db_operations.auth import check_if_non_admin_can_register
from backend_main.db_operations.login_rate_limits import add_login_rate_limit_to_request, \
    upsert_login_rate_limit, delete_login_rate_limits
from backend_main.db_operations.sessions import add_session, delete_sessions
from backend_main.db_operations.settings import view_settings
from backend_main.db_operations.users import add_user, get_user_by_credentials

from backend_main.schemas.auth import register_schema, login_schema

from backend_main.util.json import error_json, row_proxy_to_dict, serialize_datetime_to_str
from backend_main.util.login_rate_limits import get_login_attempts_timeout_in_seconds, IncorrectCredentialsException


async def register(request):
    # Debounce anonymous if non-admin registration is disabled
    await check_if_non_admin_can_register(request)

    # Validate request schema
    data = await request.json()
    validate(instance=data, schema=register_schema)

    # Check password
    if data["password"] != data["password_repeat"]:
        raise web.HTTPBadRequest(text=error_json(f"Password is not correctly repeated."), content_type="application/json")

    # Check if non-admins are not trying to set privileges
    forbidden_attributes_for_user = ("user_level", "can_login", "can_edit_objects")
    if request.user_info.user_level != "admin":
        for attr in forbidden_attributes_for_user:
            if attr in data:
                raise web.HTTPForbidden(text=error_json(f"User privileges can only be set by admins."), content_type="application/json")
    
    # Set default values
    data.pop("password_repeat")
    data["registered_at"] = datetime.utcnow()
    if "user_level" not in data: data["user_level"] = "user"
    if "can_login" not in data: data["can_login"] = True
    if "can_edit_objects" not in data: data["can_edit_objects"] = True

    # Add the user
    result = await add_user(request, data)

    # Don't send user info if admin token was not provided (registration form processing case)
    if request.user_info.user_level != "admin": return web.Response()

    # Return new user's data in case of admin registration
    return web.json_response({"user": row_proxy_to_dict(result)})


async def login(request):
    # Check and get login rate limits
    await add_login_rate_limit_to_request(request)

    # Validate request schema
    data = await request.json()
    validate(instance=data, schema=login_schema)

    # Try to get user data
    user_data = await get_user_by_credentials(request, data["login"], data["password"])

    # User was not found
    if user_data is None:
        # Update login rate limits
        lrli = request.login_rate_limit_info
        lrli.cant_login_until = datetime.utcnow() + \
            timedelta(seconds=get_login_attempts_timeout_in_seconds(lrli.failed_login_attempts))
        lrli.failed_login_attempts += 1
        await upsert_login_rate_limit(request, lrli)

        # Raise 401 with committing database changes
        raise IncorrectCredentialsException()
    
    # User was found
    else:
        # If user can't login, raise 403
        if not user_data.can_login:
            raise web.HTTPForbidden(text=error_json("User is not allowed to login."), content_type="application/json")
        
        # Create a session
        session = await add_session(request, user_data.user_id)

        # Delete login rate limit for the request issuer
        await delete_login_rate_limits(request, [request.remote])

        # Return access token
        return web.json_response({"auth": {
            "access_token": session["access_token"],
            "access_token_expiration_time": serialize_datetime_to_str(session["expiration_time"]),
            "user_id": user_data.user_id,
            "user_level": user_data.user_level
        }})


async def logout(request):
    # Delete session (if it does not, return 200 anyway)
    await delete_sessions(request, [request.user_info.access_token])
    return web.Response()


async def get_registration_status(request):
    setting_value = (await view_settings(request, ["non_admin_registration_allowed"], disable_auth_checks=True))["non_admin_registration_allowed"]
    return web.json_response({"registration_allowed": setting_value.lower() == "true"})


def get_subapp():
    app = web.Application()
    app.add_routes([
        web.post("/register", register, name="register"),
        web.post("/login", login, name="login"),
        web.post("/logout", logout, name="logout"),
        web.get("/get_registration_status", get_registration_status, name="get_registration_status")
        ])
    return app
