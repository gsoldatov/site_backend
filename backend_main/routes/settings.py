"""
    Authorization & authentication routes.
"""
from aiohttp import web

from backend_main.auth.route_checks.settings import authorize_settings_view, \
    authorize_private_settings_return

from backend_main.domains.settings import update_settings, view_settings

from backend_main.util.json import error_json

from backend_main.types.request import Request, request_log_event_key
from backend_main.types.domains.settings import SerializedSettings
from backend_main.types.routes.settings import SettingsUpdateRequestBody, \
    SettingsViewRequestBody, SettingsViewResponseBody


async def update(request: Request) -> None:
    # Validate request body
    data = SettingsUpdateRequestBody.model_validate(await request.json())
    
    # Update settings
    await update_settings(request, data.settings)
    updated_settings = data.settings.model_dump(exclude_none=True)
    request[request_log_event_key]("INFO", "route_handler", "Updated settings.", details=f"{updated_settings}")


async def view(request: Request) -> SettingsViewResponseBody:
    # Validate request body
    data = SettingsViewRequestBody.model_validate(await request.json())

    # Authorize returning all settings
    authorize_settings_view(request, data)
    
    # Query and deserialize settings
    setting_names = None if data.view_all else data.setting_names
    settings_list = await view_settings(request, setting_names)

    # Handle 404
    if len(settings_list) == 0:
        msg = "Setting(-s) not found."
        request[request_log_event_key]("WARNING", "route_handler", msg, details=f"{setting_names}")
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")
    
    # Authorize return of private settings
    # (don't double check, if `view_all` was set to true in the request)
    if not data.view_all:
        authorize_private_settings_return(request, settings_list)
    
    # Serialize & return settings
    serialized_settings = SerializedSettings.from_setting_list(settings_list)
    request[request_log_event_key]("INFO", "route_handler", "Returning settings.")
    return SettingsViewResponseBody(settings=serialized_settings)


def get_subapp():
    app = web.Application()
    app.add_routes([
        web.put("/update", update, name="update"),
        web.post("/view", view, name="view")
        ])
    return app
