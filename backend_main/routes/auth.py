"""
    Authorization & authentication routes.
"""
from aiohttp import web

from backend_main.auth.route_checks import ensure_non_admin_can_register

from backend_main.domains.auth.register import validate_new_user_data
from backend_main.domains.login_rate_limits import get_request_sender_login_rate_limit, \
    increase_request_sender_login_rate_limit, delete_request_sender_login_rate_limit
from backend_main.domains.sessions import add_session
from backend_main.domains.users import add_user, get_user_by_login_and_password

from backend_main.db_operations.sessions import delete_sessions
from backend_main.middlewares.connection import start_transaction

from backend_main.util.exceptions import InvalidNewUserAttributesException, IncorrectCredentialsException
from backend_main.util.json import error_json

from backend_main.types.routes.auth import AuthLoginRequestBody, AuthLoginResponseBody
from backend_main.types.request import Request, request_log_event_key, request_user_info_key


async def register(request: Request):
    # Debounce anonymous if non-admin registration is disabled
    await ensure_non_admin_can_register(request)

    # Validate request body and set default values
    try:
        new_user = await validate_new_user_data(request)
    except InvalidNewUserAttributesException:
        msg = "User privileges can only be set by admins."
        request[request_log_event_key]("WARNING", "route_handler", msg)
        raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
    
    # Add user
    user = await add_user(request, new_user)
    request[request_log_event_key]("INFO", "route_handler", f"Registered user {user.user_id}.")

    # Don't send user info if admin token was not provided (registration form processing case)
    if request[request_user_info_key].user_level != "admin": return web.Response()

    # Return new user's data in case of admin registration
    return web.json_response({
        "user": user.model_dump()
    })


async def login(request: Request):
    # Check and get login rate limits
    login_rate_limit = await get_request_sender_login_rate_limit(request)

    # Validate request data and get user
    try:
        data = await request.json()
        credentials = AuthLoginRequestBody(**data)
        user = await get_user_by_login_and_password(request, credentials.login, credentials.password)
    except IncorrectCredentialsException:
        # Raise `IncorrectCredentialsException` after increasing login rate limit below
        user = None

    # User was not found
    if user is None:
        # Raise 401 with committing database changes
        await increase_request_sender_login_rate_limit(request, login_rate_limit)
        request[request_log_event_key]("WARNING", "route_handler", f"Incorrect user credentials.")
        raise IncorrectCredentialsException()
    
    # User was found
    else:
        # User can't login
        if not user.can_login:
            msg = "User is not allowed to login."
            request[request_log_event_key]("WARNING", "route_handler", msg)
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
        
        # Start a transaction
        await start_transaction(request)
        
        # Create a session
        session = await add_session(request, user.user_id)

        # Delete login rate limit for the request issuer
        await delete_request_sender_login_rate_limit(request)

        # Return auth data
        request[request_log_event_key]("INFO", "route_handler", f"User {user.user_id} logged in.")

        auth_data = AuthLoginResponseBody(**{"auth": {
            "access_token": session.access_token,
            "access_token_expiration_time": session.expiration_time,
            "user_id": user.user_id,
            "user_level": user.user_level
        }})

        return web.json_response(auth_data.model_dump())


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
