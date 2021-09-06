"""
Auth-related database operations.
"""
from datetime import datetime, timedelta

from aiohttp import web
from sqlalchemy import select, true
from sqlalchemy.sql import and_ 

from backend_main.auth.route_access_checks.util import debounce_anonymous


async def prolong_token_and_get_user_info(request):
    """
    Gets user information for the provided access token and adds it to `request.user_info`.
    Raises 401 if token is not found or expired.
    Prolongs the lifetime of the token if otherwise.
    """
    # Exit if anonymous
    if request.user_info.is_anonymous:
        return
    
    users = request.app["tables"]["users"]
    sessions = request.app["tables"]["sessions"]
    current_time = datetime.utcnow()
    expiration_time = current_time + timedelta(seconds=request.app["config"]["app"]["token_lifetime"])

    # Update expiration time and return user information corresponding to the updated token 
    # in a single query using CTE.
    # NOTE: values updated in CTE can't be fetched with select in the same query.
    update_cte = (
        sessions.update()
        .where(and_(
            sessions.c.access_token == request.user_info.access_token,
            sessions.c.expiration_time > current_time
        ))
        .values({"expiration_time": expiration_time})
        .returning(sessions.c.user_id.label("user_id"))
    ).cte("update_cte")

    result = await request["conn"].execute(
        select([users.c.user_id, users.c.user_level, users.c.can_edit_objects])
        .where(users.c.user_id.in_(select([update_cte.c.user_id])))
    )

    info = await result.fetchone()

    # Raise 401 if token was not found or expired
    if not info:
        raise web.HTTPUnauthorized(text=error_json("Invalid token."), content_type="application/json")
    
    ui = request.user_info
    ui.user_id, ui.user_level, ui.can_edit_objects = info[0], info[1], info[2]


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
        objects = request.app["tables"]["objects"]
        user_id = request.user_info.user_id

        result = await request["conn"].execute(
            select([objects.c.object_id, objects.c.owner_id])
            .where(objects.c.object_id.in_(object_ids))
        )

        not_owned_objects = [o[0] for o in await result.fetchall() if o[1] != user_id]

        if len(not_owned_objects) > 0:
            raise web.HTTPForbidden(text=error_json(f"User ID '{user_id} does not own object_ids {not_owned_objects}."), content_type="application/json")


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
        objects = request.app["tables"]["objects"]
        objects_tags = request.app["tables"]["objects_tags"]
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
            raise web.HTTPForbidden(text=error_json(f"User ID '{user_id} does not own object_ids {not_owned_objects}."), content_type="application/json")


def get_objects_auth_filter_clause(request):
    """
    Returns an SQLAlchemy where clause, which:
    - filters non-published objects is user is anonymous;
    - filters non-published objects of other users if user has 'user' level;
    - 1 = 1 for 'admin' user level.
    """
    objects = request.app["tables"]["objects"]
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
    - filters objects with provided `object_ids`, which are non-published and belong to other users if user has 'user' level;
    - filters objects with provided `object_ids`, which are non-published if user is anonymous.
    """
    objects = request.app["tables"]["objects"]
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
