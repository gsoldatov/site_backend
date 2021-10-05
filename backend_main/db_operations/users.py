"""
User-related database operations.
"""
from aiohttp import web
from sqlalchemy import select, and_
from sqlalchemy.sql import text

from backend_main.auth.route_access_checks.util import debounce_anonymous

from backend_main.db_operations.sessions import delete_sessions

from backend_main.util.constants import forbidden_non_admin_user_modify_attributes
from backend_main.util.json import error_json


async def get_user_by_credentials(request, user_id = None, login = None, password = None):
    """
    Returns information about the user with provided `user_id`/`login` and `password`, if he exists.
    """
    # Raise if provided arguments are incorrect
    if user_id is None and login is None: raise TypeError("Either `user_id` or `login` must be provided.")
    if password is None: raise TypeError("`password` must be provided.")

    # Exit if argument values are incorrect
    if len(password) < 8 or len(password) > 72: return None
    
    users = request.config_dict["tables"]["users"]
    user_id_or_login_clause = users.c.user_id == user_id if user_id is not None else users.c.login == login
    password_clause = text("password = crypt(:submitted_password, password)")

    result = await request["conn"].execute(
        select([users.c.user_id, users.c.username, users.c.user_level, 
            users.c.can_login, users.c.can_edit_objects])
        .where(and_(
            user_id_or_login_clause,
            password_clause
        ))
    , submitted_password=password)  # password is passed as a bind parameter in order to escape it
    return await result.fetchone()


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


async def update_user(request, data):
    """
    Updates an existing user with properties specified in `data`.
    """
    # Check if token owner can update data
    if request.user_info.user_level != "admin":
        if request.user_info.user_id != data["user"]["user_id"]:
            raise web.HTTPForbidden(text=error_json("Non-admin users are not allowed to update information of other users."), content_type="application/json")
        
        for attr in forbidden_non_admin_user_modify_attributes:
            if attr in data: raise web.HTTPForbidden(text=error_json(f"User privileges can only be set by admins."), content_type="application/json")
    
    # Additional data validation
    if "password" in data["user"]:
        if data["user"]["password"] != data["user"]["password_repeat"]:
            raise web.HTTPBadRequest(text=error_json(f"Password is not correctly repeated."), content_type="application/json")
    
    # Check if token owner submitted a correct password
    if await get_user_by_credentials(request, user_id=request.user_info.user_id, password=data["token_owner_password"]) is None:
        raise web.HTTPBadRequest(text=error_json(f"Token owner password is incorrect."), content_type="application/json")
    
    # Update user
    users = request.config_dict["tables"]["users"]
    values = {k: data["user"][k] for k in ("login", "username", "user_level", "can_login", "can_edit_objects") if k in data["user"]}
    if "password" in data["user"]:
        values["password"] = text("crypt(:password, gen_salt('bf'))")
    
    result = await request["conn"].execute(
        users.update()
        .where(users.c.user_id == data["user"]["user_id"])
        .values(values)
        .returning(users.c.user_id)
    , password=data["user"].get("password"))    # password is passed as a bind parameter in order to escape it

    # Handle user not found case
    if not await result.fetchone():
        raise web.HTTPNotFound(text=error_json(f"User not found."), content_type="application/json")
    
    # Clear existing sessions if user can no longer login
    if data["user"].get("can_login") == False:
        await delete_sessions(request, user_ids=[data["user"]["user_id"]])
    
    return


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

    columns = [users.c.user_id, users.c.registered_at, users.c.username, users.c.user_level, users.c.can_login, users.c.can_edit_objects] \
        if full_view_mode else [users.c.user_id, users.c.registered_at, users.c.username]
    
    result = await request["conn"].execute(
        select(columns)
        .where(users.c.user_id.in_(user_ids))
    )
    return await result.fetchall()
