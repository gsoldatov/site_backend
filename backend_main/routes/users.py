from aiohttp import web
from typing import cast

from backend_main.domains.sessions import delete_user_sessions
from backend_main.domains.users import validate_user_update, check_password_for_user_id, update_user, view_users

from backend_main.middlewares.connection import start_transaction

from backend_main.util.exceptions import UserFullViewModeNotAllowed
from backend_main.util.json import error_json

from backend_main.types.domains.users import UserUpdate
from backend_main.types.routes.users import UsersUpdateRequestBody, UsersViewRequestBody, UsersViewResponseBody
from backend_main.types.request import Request, request_log_event_key, request_user_info_key


async def update(request: Request) -> None:
    # Validate request body
    data = UsersUpdateRequestBody.model_validate(await request.json())
    user_update = UserUpdate.model_validate(data.user, from_attributes=True)

    # Check if token owner can update data
    validate_user_update(request, user_update)

    # Ensure a transaction is started
    await start_transaction(request)

    # Check if token owner submitted a correct password
    token_owner_user_id = cast(int, request[request_user_info_key].user_id)
    await check_password_for_user_id(request, token_owner_user_id, data.token_owner_password)

    # Perform user update
    user_id = await update_user(request, user_update)
    if user_id is None:
        raise web.HTTPNotFound(text=error_json(f"User not found."), content_type="application/json")
    
    # Delete user sessions, if he can no longer log in
    if user_update.can_login == False:
        await delete_user_sessions(request, user_update.user_id)
    
    request[request_log_event_key]("INFO", "route_handler", "Updated user.", details=f"user_id = {user_update.user_id}")


async def view(request: Request) -> UsersViewResponseBody:
    # Validate request body
    data = UsersViewRequestBody.model_validate(await request.json())

    # Query data
    try:
        users = await view_users(request, data.user_ids, data.full_view_mode)
    except UserFullViewModeNotAllowed:
        msg = "Attempted to view full information about other users as a non-admin."
        request[request_log_event_key]("WARNING", "db_operation", msg)
        raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
    
    # Handle 404
    if len(users) == 0:
        msg = "Users not found."
        request[request_log_event_key]("WARNING", "route_handler", msg, details=f"user_ids = {data.user_ids}")
        raise web.HTTPNotFound(text=error_json("Users not found."), content_type="application/json")
    
    request[request_log_event_key]("INFO", "route_handler", "Returning users.", details=f"user_ids = {data.user_ids}")
    return UsersViewResponseBody.model_validate({"users": users})


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.put("/update", update, name="update"),
                    web.post("/view", view, name="view")
                ])
    return app
