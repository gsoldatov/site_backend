from aiohttp import web
from jsonschema import validate

from backend_main.db_operations.users import update_user
from backend_main.domains.users import view_users

from backend_main.util.exceptions import UserFullViewModeNotAllowed
from backend_main.util.json import error_json

from backend_main.types.routes.users import UsersViewRequestBody, UsersViewResponseBody
from backend_main.validation.schemas.users import users_update_schema
from backend_main.types.request import Request, request_log_event_key


async def update(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=users_update_schema)

    # Perform additional data validation & update data
    await update_user(request, data)
    request[request_log_event_key]("INFO", "route_handler", "Updated user.", details=f"user_id = {data['user']['user_id']}")
    return {}


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
