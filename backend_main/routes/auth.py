"""
    Authorization & authentication route handlers.
"""
from aiohttp import web

from backend_main.auth.route_checks.auth import authorize_user_registration_with_privileges_set, \
    authorize_user_registration_by_non_admin

from backend_main.domains.login_rate_limits import get_request_sender_login_rate_limit, \
    increase_request_sender_login_rate_limit, delete_request_sender_login_rate_limit
from backend_main.domains.sessions import add_session, delete_session_by_access_token
from backend_main.domains.users import add_user, get_user_by_login_and_password

from backend_main.util.exceptions import IncorrectCredentialsException
from backend_main.util.json import error_json

from backend_main.types.app import app_start_transaction_key
from backend_main.types.request import Request, request_log_event_key, request_user_info_key, request_time_key
from backend_main.types.domains.users import NewUser
from backend_main.types.routes.auth import AuthRegisterRequestBody, AuthLoginRequestBody, AuthLoginResponseBody


async def register(request: Request) -> web.Response:
    # Forbid non-admin registration, if its not enabled
    await authorize_user_registration_by_non_admin(request)

    # Validate request body
    data = AuthRegisterRequestBody.model_validate(await request.json())

    # Check if non-admins are trying to set privileges
    authorize_user_registration_with_privileges_set(request, data)

    # Set default values & convert to insert format
    new_user = NewUser.model_validate({
        **{
            "registered_at": request[request_time_key],
            "user_level": "user",
            "can_login": True,
            "can_edit_objects": True
        },
        **data.model_dump(exclude_none=True)
    })
    
    # Add user
    user = await add_user(request, new_user)
    request[request_log_event_key]("INFO", "route_handler", f"Registered user {user.user_id}.")

    # Don't send user info if admin token was not provided (registration form processing case)
    if request[request_user_info_key].user_level != "admin": return web.Response()

    # Return new user's data in case of admin registration
    return web.json_response({
        "user": user.model_dump()
    })


async def login(request: Request) -> web.Response:
    # Check and get login rate limits
    login_rate_limit = await get_request_sender_login_rate_limit(request)

    # Validate request data and get user
    try:
        data = await request.json()
        credentials = AuthLoginRequestBody(**data)
       
        # Start a transaction
        await request.config_dict[app_start_transaction_key](request)
        
        user = await get_user_by_login_and_password(request, credentials.login, credentials.password)
    except IncorrectCredentialsException:
        # Raise `IncorrectCredentialsException` after increasing login rate limit below
        user = None

    # User was not found
    if user is None:
        # Raise 401 with committing database changes
        await increase_request_sender_login_rate_limit(request, login_rate_limit)
        msg = "Incorrect login or password."
        request[request_log_event_key]("WARNING", "route_handler", msg)
        raise IncorrectCredentialsException(msg)
    
    # User was found
    else:
        # User can't login
        if not user.can_login:
            msg = "User is not allowed to login."
            request[request_log_event_key]("WARNING", "route_handler", msg)
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
        
        # Create a session
        session = await add_session(request, user.user_id)

        # Delete login rate limit for the request issuer
        await delete_request_sender_login_rate_limit(request)

        # Return auth data
        request[request_log_event_key]("INFO", "route_handler", f"User {user.user_id} logged in.")

        auth_data = AuthLoginResponseBody.model_validate({"auth": {
            "access_token": session.access_token,
            "access_token_expiration_time": session.expiration_time,
            "user_id": user.user_id,
            "user_level": user.user_level
        }})

        return web.json_response(auth_data.model_dump())


async def logout(request: Request) -> web.Response:
    # Delete session (if it does not exist, return 200 anyway)
    user_info = request[request_user_info_key]
    await delete_session_by_access_token(request, user_info.access_token)
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
