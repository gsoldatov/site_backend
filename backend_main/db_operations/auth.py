"""
Auth-related database operations and SQLAlchemy constructs.
"""
from aiohttp import web
from sqlalchemy import select, true
from sqlalchemy.sql import and_, or_

from backend_main.app.types import app_tables_key
from backend_main.auth.route_access_checks.util import debounce_anonymous
from backend_main.db_operations.settings import view_settings
from backend_main.util.json import error_json


async def check_if_user_owns_objects(request, object_ids):
    """
    Checks is `request["user_info"].user_id` is admin or user owning all objects with the provided `object_ids`.
    Raises 401 for anonymous.
    Raises 403 if user is not admin and does not own at least one object. Non-existing objects do not trigger the exception.
    """
    if len(object_ids) == 0:
        return
    
    debounce_anonymous(request)

    if request["user_info"].user_level != "admin":
        objects = request.config_dict[app_tables_key].objects
        user_id = request["user_info"].user_id

        result = await request["conn"].execute(
            select(objects.c.object_id, objects.c.owner_id)
            .where(objects.c.object_id.in_(object_ids))
        )

        not_owned_objects = [o[0] for o in await result.fetchall() if o[1] != user_id]

        if len(not_owned_objects) > 0:
            msg = "User does not own object(-s)."
            request["log_event"]("WARNING", "auth", msg, details=f"user_id = {user_id}, object_ids = {not_owned_objects}")
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


async def check_if_user_owns_all_tagged_objects(request, tag_ids):
    """
    Checks is `request["user_info"].user_id` is admin or user owning all objects tagged with the provided `tag_ids`.
    Raises 401 for anonymous.
    Raises 403 if user is not admin and does not own at least one object.
    """
    if len(tag_ids) == 0:
        return

    debounce_anonymous(request)

    if request["user_info"].user_level != "admin":
        objects = request.config_dict[app_tables_key].objects
        objects_tags = request.config_dict[app_tables_key].objects_tags
        user_id = request["user_info"].user_id

        result = await request["conn"].execute(
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
            request["log_event"]("WARNING", "auth", msg, details=f"user_id = {user_id}, object_ids = {not_owned_objects}")
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


async def check_if_non_admin_can_register(request):
    """
    Checks if non-admin registration is enabled.
    If request was not sent by an admin and registration is not enabled, raises 403.
    """
    if request["user_info"].user_level == "admin": return

    non_admin_registration_allowed = (await view_settings(request, ["non_admin_registration_allowed"]))["non_admin_registration_allowed"]

    if not non_admin_registration_allowed:
        msg = "Registration is disabled."
        request["log_event"]("WARNING", "auth", msg)
        raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


def get_objects_auth_filter_clause(request, object_ids = None, object_ids_subquery = None):
    """
    Returns an SQLAlchemy 'where' clause, which:
    - filters non-published objects and objects with non-published tags if user is anonymous;
    - filters non-published objects of other users and objects with non-published tags if user has 'user' level;
    - 1 = 1 for 'admin' user level.

    `object_ids` or `object_ids_subquery` are used to specify object IDs, which are checked for being marked with non-published tags.
    """
    objects = request.config_dict[app_tables_key].objects
    ui = request["user_info"]

    if ui.is_anonymous:
        return and_(
            objects.c.is_published == True,
            get_objects_with_published_tags_only_clause(request, object_ids, object_ids_subquery)
        )
    
    if ui.user_level == "admin":
        return true()
    
    # user
    return and_(
        or_(objects.c.owner_id == ui.user_id, objects.c.is_published == True),
        get_objects_with_published_tags_only_clause(request, object_ids, object_ids_subquery)
    )


def get_objects_data_auth_filter_clause(request, object_id_column, object_ids):
    """
    Returns an SQL Alchemy 'where' clause with a subquery for applying objects' auth filters for `object_id_column`.
    """
    objects = request.config_dict[app_tables_key].objects
    ui = request["user_info"]

    if ui.user_level == "admin":
        return object_id_column.in_(object_ids)
    
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

    return object_id_column.in_(
        select(objects.c.object_id)
        .where(and_(
            objects_auth_filter_clause,
            objects.c.object_id.in_(object_ids)
        ))
    )


def get_objects_with_published_tags_only_clause(request, object_ids = None, object_ids_subquery = None):
    """
    Returns an SQL Alchemy 'where' clause subquery, which:
    - if user has admin level, does nothing;
    - if user has non-admin level, filters `objects.object_id` column with a subquery, 
      which filters out IDs with at least one non-published tag.
    
    To reduce the amount of objects' tags processing an iterable with object IDs `object_ids`
    or a subquery, which returns a list of object IDs `object_ids_subquery` must be provided.
    """
    if object_ids is None and object_ids_subquery is None:
        raise RuntimeError("Either `object_ids` or `object_ids_subquery` must be provided.")
    
    objects = request.config_dict[app_tables_key].objects
    tags = request.config_dict[app_tables_key].tags
    objects_tags = request.config_dict[app_tables_key].objects_tags
    ui = request["user_info"]

    if ui.user_level == "admin": return true()

    object_ids_filter = object_ids if object_ids is not None else object_ids_subquery

    return objects.c.object_id.notin_(
        select(objects_tags.c.object_id)
        .distinct()
        .select_from(objects_tags.join(tags, objects_tags.c.tag_id == tags.c.tag_id))
        .where(and_(
            objects_tags.c.object_id.in_(object_ids_filter),
            get_tags_auth_filter_clause(request, is_published=False)
        ))
    )


def get_tags_auth_filter_clause(request, is_published = True):
    """
    Returns an SQL Alchemy 'where' clause for filtering tags on `is_published` field with the provided `is_published` value:
    - 1 = 1 for admin user level;
    - tags.is_published = `is_published` if user has 'user' level;
    - tags.is_published = `is_published` if user is anonymous.
    """
    tags = request.config_dict[app_tables_key].tags
    ui = request["user_info"]

    if ui.user_level == "admin": return true()

    return tags.c.is_published == is_published
