"""
Route auth checks, which rely on request data.
"""
from aiohttp import web
from sqlalchemy import select

from backend_main.auth.route_access.common import forbid_anonymous
from backend_main.db_operations.settings import view_settings
from backend_main.util.json import error_json

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_log_event_key, request_user_info_key, request_connection_key


async def ensure_user_can_edit_objects(request: Request, object_ids: list[int]):
    """
    Checks is `request[request_user_info_key].user_id` is an admin or a user owning all objects with the provided `object_ids`.
    Raises 401 for anonymous.
    Raises 403 if user is not admin and does not own at least one object. Non-existing objects do not trigger the exception.
    """
    if len(object_ids) == 0:
        return
    
    forbid_anonymous(request)

    if request[request_user_info_key].user_level != "admin":
        objects = request.config_dict[app_tables_key].objects
        user_id = request[request_user_info_key].user_id

        result = await request[request_connection_key].execute(
            select(objects.c.object_id, objects.c.owner_id)
            .where(objects.c.object_id.in_(object_ids))
        )

        not_owned_objects = [o[0] for o in await result.fetchall() if o[1] != user_id]

        if len(not_owned_objects) > 0:
            msg = "User does not own object(-s)."
            request[request_log_event_key]("WARNING", "auth", msg, details=f"user_id = {user_id}, object_ids = {not_owned_objects}")
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


async def ensure_user_can_edit_all_tagged_objects(request: Request, tag_ids: list[int]):
    """
    Checks is `request[request_user_info_key].user_id` is an admin or a user owning all objects tagged with the provided `tag_ids`.
    Raises 401 for anonymous.
    Raises 403 if user is not admin and does not own at least one object.
    """
    if len(tag_ids) == 0:
        return

    forbid_anonymous(request)

    if request[request_user_info_key].user_level != "admin":
        objects = request.config_dict[app_tables_key].objects
        objects_tags = request.config_dict[app_tables_key].objects_tags
        user_id = request[request_user_info_key].user_id

        result = await request[request_connection_key].execute(
            select(objects.c.object_id, objects.c.owner_id)
            .where(objects.c.object_id.in_(
                select(objects_tags.c.object_id)
                .distinct()
                .where(objects_tags.c.tag_id.in_(tag_ids))
            ))
        )

        not_owned_objects = [o[0] for o in await result.fetchall() if o[1] != user_id]

        if len(not_owned_objects) > 0:
            msg = "User does not own object(-s)."
            request[request_log_event_key]("WARNING", "auth", msg, details=f"user_id = {user_id}, object_ids = {not_owned_objects}")
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


async def ensure_non_admin_can_registed(request: Request):
    """
    Checks if non-admin registration is enabled.
    If request was not sent by an admin and registration is not enabled, raises 403.
    """
    if request[request_user_info_key].user_level == "admin": return

    non_admin_registration_allowed = (await view_settings(request, ["non_admin_registration_allowed"]))["non_admin_registration_allowed"]

    if not non_admin_registration_allowed:
        msg = "Registration is disabled."
        request[request_log_event_key]("WARNING", "auth", msg)
        raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
