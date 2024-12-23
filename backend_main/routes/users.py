from backend_main.util.json import row_proxy_to_dict
from aiohttp import web
from jsonschema import validate

from backend_main.db_operations.users import update_user, view_users

from backend_main.validation.schemas.users import users_update_schema, users_view_schema

from backend_main.util.json import row_proxy_to_dict, error_json

from backend_main.types.request import request_log_event_key


async def update(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=users_update_schema)

    # Perform additional data validation & update data
    await update_user(request, data)
    request[request_log_event_key]("INFO", "route_handler", "Updated user.", details=f"user_id = {data['user']['user_id']}")
    return {}


async def view(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=users_view_schema)

    # Set view mode if it's omitted
    full_view_mode = False if "full_view_mode" not in data else data["full_view_mode"]

    # Query and serialize data
    users = [row_proxy_to_dict(row) for row in await view_users(request, data["user_ids"], full_view_mode)]

    # Handle 404
    if len(users) == 0:
        msg = "Users not found."
        request[request_log_event_key]("WARNING", "route_handler", msg, details=f"user_ids = {data['user_ids']}")
        raise web.HTTPNotFound(text=error_json("Users not found."), content_type="application/json")
    
    request[request_log_event_key]("INFO", "route_handler", "Returning users.", details=f"user_ids = {data['user_ids']}")
    return {"users": users}


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.put("/update", update, name="update"),
                    web.post("/view", view, name="view")
                ])
    return app
