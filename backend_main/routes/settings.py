"""
    Authorization & authentication routes.
"""
from aiohttp import web
from jsonschema import validate

from backend_main.db_operations.settings import update_settings, view_settings

from backend_main.validation.schemas.settings import settings_view_schema, settings_update_schema

from backend_main.util.json import error_json

from backend_main.types.request import request_log_event_key


async def update(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=settings_update_schema)
    if len(data["settings"]) == 0:
        msg = "At least one setting must be passed for updating."
        request[request_log_event_key]("WARNING", "route_handler", msg)
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")
    
    # Update settings
    await update_settings(request, data["settings"])
    request[request_log_event_key]("INFO", "route_handler", "Updated settings.", details=f"{data['settings']}")

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
        msg = "Setting(-s) not found."
        request[request_log_event_key]("WARNING", "route_handler", msg, details=f"{setting_names}")
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")
    
    request[request_log_event_key]("INFO", "route_handler", "Returning settings.")
    return {"settings": deserialized_settings}


def get_subapp():
    app = web.Application()
    app.add_routes([
        web.put("/update", update, name="update"),
        web.post("/view", view, name="view")
        ])
    return app
