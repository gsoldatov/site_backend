"""
Auth-related database operations and SQLAlchemy constructs.
"""
from aiohttp import web
from sqlalchemy import select, true
from sqlalchemy.sql import and_, or_

from backend_main.auth.route_access_checks.util import debounce_anonymous
from backend_main.db_operations.settings import view_settings
from backend_main.util.json import error_json


async def check_if_user_owns_objects(request, object_ids):
    """
    Checks is `request.user_info.user_id` is admin or user owning all objects with the provided `object_ids`.
    Raises 401 for anonymous.
    Raises 403 if user is not admin and does not own at least one object. Non-existing objects do not trigger the exception.
    """
    if len(object_ids) == 0:
        return
    
    debounce_anonymous(request)

    if request.user_info.user_level != "admin":
        objects = request.config_dict["tables"]["objects"]
        user_id = request.user_info.user_id

        result = await request["conn"].execute(
            select([objects.c.object_id, objects.c.owner_id])
            .where(objects.c.object_id.in_(object_ids))
        )

        not_owned_objects = [o[0] for o in await result.fetchall() if o[1] != user_id]

        if len(not_owned_objects) > 0:
            msg = "User does not own object(-s)."
            request.log_event("WARNING", "auth", msg, details=f"user_id = {user_id}, object_ids = {not_owned_objects}")
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


async def check_if_user_owns_all_tagged_objects(request, tag_ids):
    """
    Checks is `request.user_info.user_id` is admin or user owning all objects tagged with the provided `tag_ids`.
    Raises 401 for anonymous.
    Raises 403 if user is not admin and does not own at least one object.
    """
    if len(tag_ids) == 0:
        return

    debounce_anonymous(request)

    if request.user_info.user_level != "admin":
        objects = request.config_dict["tables"]["objects"]
        objects_tags = request.config_dict["tables"]["objects_tags"]
        user_id = request.user_info.user_id

        result = await request["conn"].execute(
            select([objects.c.object_id, objects.c.owner_id])
            .where(objects.c.object_id.in_(
                select([objects_tags.c.object_id])
                .distinct()
                .where(objects_tags.c.tag_id.in_(tag_ids))
            ))
        )

        not_owned_objects = [o[0] for o in await result.fetchall() if o[1] != user_id]

        if len(not_owned_objects) > 0:
            msg = "User does not own object(-s)."
            request.log_event("WARNING", "auth", msg, details=f"user_id = {user_id}, object_ids = {not_owned_objects}")
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


def get_objects_auth_filter_clause(request):
    """
    Returns an SQLAlchemy where clause, which:
    - filters non-published objects is user is anonymous;
    - filters non-published objects of other users if user has 'user' level;
    - 1 = 1 for 'admin' user level.
    """
    objects = request.config_dict["tables"]["objects"]
    ui = request.user_info

    if ui.is_anonymous:
        return objects.c.is_published == True
    
    if ui.user_level == "admin":
        return true()
    
    # user
    return or_(objects.c.owner_id == ui.user_id, objects.c.is_published == True)


def get_objects_data_auth_filter_clause(request, object_ids, object_id_column):
    """
    Returns and SQL Alchemy where clause with a subquery for a specified `object_data_table`, which:
    - filters objects with provided `object_ids` if user has `admin` level;
    - filters objects with provided `object_ids`, which are not published and belong to other users if user has 'user' level;
    - filters objects with provided `object_ids`, which are not published if user is anonymous.
    """
    objects = request.config_dict["tables"]["objects"]
    ui = request.user_info

    if ui.user_level == "admin":
        return object_id_column.in_(object_ids)
    
    auth_filter_clause = get_objects_auth_filter_clause(request)

    return object_id_column.in_(
        select([objects.c.object_id])
        .where(and_(
            auth_filter_clause,
            objects.c.object_id.in_(object_ids)
        ))
    )


async def check_if_non_admin_can_register(request):
    """
    Checks if non-admin registration is enabled.
    If request was not sent by an admin and registration is not enabled, raises 403.
    """
    if request.user_info.user_level == "admin": return

    non_admin_registration_allowed = (await view_settings(request, ["non_admin_registration_allowed"]))["non_admin_registration_allowed"]

    if not non_admin_registration_allowed:
        msg = "Registration is disabled."
        request.log_event("WARNING", "auth", msg)
        raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
