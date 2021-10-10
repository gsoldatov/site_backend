"""
    Authorization & authentication routes.
"""
from aiohttp import web
from jsonschema import validate

from backend_main.db_operations.settings import update_settings, view_settings

from backend_main.schemas.settings import settings_view_schema, settings_update_schema

from backend_main.util.json import error_json


async def update(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=settings_update_schema)
    if len(data["settings"]) == 0:
        raise web.HTTPBadRequest(text=error_json(f"At least one setting must be passed for updating."), content_type="application/json")
    
    # Update settings
    await update_settings(request, data["settings"])

    # Return an empty response body
    return {}


async def view(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=settings_view_schema)
    
    # Query and deserialize settings
    setting_names = None if data.get("view_all", False) else data["setting_names"]
    deserialized_settings = await view_settings(request, setting_names)

    # Handle 404
    if len(deserialized_settings) == 0:
        raise web.HTTPNotFound(text=error_json(f"Setting(-s) not found."), content_type="application/json")
    
    return {"settings": deserialized_settings}


def get_subapp():
    app = web.Application()
    app.add_routes([
        web.put("/update", update, name="update"),
        web.post("/view", view, name="view")
        ])
    return app
