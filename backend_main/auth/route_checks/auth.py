"""
/auth/... route auth checks, which rely on request data.
"""
from aiohttp import web

from backend_main.db_operations.settings import view_settings
from backend_main.util.constants import forbidden_non_admin_user_modify_attributes
from backend_main.util.json import error_json

from backend_main.types.routes.auth import AuthRegisterRequestBody
from backend_main.types.request import Request, request_log_event_key, request_user_info_key


async def authorize_user_registration_by_non_admin(request: Request):
    """
    Checks if user registration is enabled for non-admins.
    If request was not sent by an admin and registration is not enabled, raises 403.
    """
    if request[request_user_info_key].user_level == "admin": return

    non_admin_registration_allowed = (await view_settings(request, ["non_admin_registration_allowed"]))["non_admin_registration_allowed"]

    if not non_admin_registration_allowed:
        msg = "Registration is disabled."
        request[request_log_event_key]("WARNING", "auth", msg)
        raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


def authorize_user_registration_with_privileges_set(request: Request, request_data: AuthRegisterRequestBody):
    """
    Checks if user registration by non-admins does not contain user privilege settings.
    """
    if request[request_user_info_key].user_level == "admin": return

    for attr in forbidden_non_admin_user_modify_attributes:
        if getattr(request_data, attr) is not None:
            msg = "User privileges can only be set by admins."
            request[request_log_event_key]("WARNING", "auth", msg)
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
