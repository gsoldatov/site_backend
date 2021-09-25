"""
User-related database operations.
"""
from aiohttp import web
from sqlalchemy import select, and_
from sqlalchemy.sql import text

from backend_main.auth.route_access_checks.util import debounce_anonymous

from backend_main.util.json import error_json


async def add_user(request, data):
    """
    Adds a user with properties specified in `data` to the database.
    All auth and data checks are performed in /auth/register route handler.
    """
    users = request.config_dict["tables"]["users"]

    # Use encryption function on the password
    password = data["password"]
    data["password"] = text("crypt(:password, gen_salt('bf'))")

    result = await request["conn"].execute(
        users.insert()
        .returning(users.c.user_id, users.c.registered_at, users.c.login, users.c.username,
                users.c.user_level, users.c.can_login, users.c.can_edit_objects)
        .values(data)
    , password=password)    # password is passed as a bind parameter in order to escape it
    return await result.fetchone()


async def get_user_by_credentials(request, login, password):
    """
    Returns information about the user with provided `login` and `password`, if he exists.
    """
    # Exit if password has incorrect length
    if len(password) < 8 or len(password) > 72: return None
    
    users = request.config_dict["tables"]["users"]
    password_clause = text("password = crypt(:submitted_password, password)")

    result = await request["conn"].execute(
        select([users.c.user_id, users.c.username, users.c.user_level, 
            users.c.can_login, users.c.can_edit_objects])
        .where(and_(
            users.c.login == login,
            password_clause
        ))
    , submitted_password=password)  # password is passed as a bind parameter in order to escape it
    return await result.fetchone()


async def check_if_user_ids_exist(request, user_ids):
    """
    Checks if provided `user_id` exists in the database.
    Raises 400 if not.
    """
    if len(user_ids) == 0: return
    users = request.config_dict["tables"]["users"]

    result = await request["conn"].execute(
        select([users.c.user_id])
        .where(users.c.user_id.in_(user_ids))
    )
    existing_user_ids = set((r[0] for r in await result.fetchall()))

    if len(user_ids) > len(existing_user_ids):
        non_existing_user_ids = set(user_ids).difference(existing_user_ids)
        raise web.HTTPBadRequest(text=error_json(f"User IDs '{non_existing_user_ids}' do not exist."), content_type="application/json")


async def view_users(request, user_ids, full_view_mode):
    """
    Returns an iterable with RowProxy objects with user information for the provided `user_ids`.
    If `full_view_mode` is true, returns full information about user, otherwise - only `username` and `registered_at`.
    `full_view_mode` == true can only be used by admins or users viewing their own information.
    """
    # Check if operation is authorized
    if full_view_mode:
        debounce_anonymous(request)
        
        if request.user_info.user_level != "admin":
            if len(user_ids) > 1 or user_ids[0] != request.user_info.user_id:
                raise web.HTTPForbidden(text=error_json("Non-admin users are not allowed to view full information about other users."), content_type="application/json")

    # Query and return data
    users = request.config_dict["tables"]["users"]

    columns = [users.c.user_id, users.c.registered_at, users.c.login, users.c.username, users.c.user_level, users.c.can_login, users.c.can_edit_objects] \
        if full_view_mode else [users.c.user_id, users.c.registered_at, users.c.username]
    
    result = await request["conn"].execute(
        select(columns)
        .where(users.c.user_id.in_(user_ids))
    )
    return await result.fetchall()
