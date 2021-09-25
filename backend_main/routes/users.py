from backend_main.util.json import row_proxy_to_dict
from aiohttp import web
from jsonschema import validate

from backend_main.db_operations.users import view_users

from backend_main.schemas.users import users_view_schema

from backend_main.util.json import row_proxy_to_dict, error_json


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
        raise web.HTTPNotFound(text=error_json("Users not found."), content_type="application/json")
    
    return {"users": users}


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("/view", view, name = "view")
                ])
    return app
