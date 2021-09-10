"""
User-related database operations.
"""
from aiohttp import web
from sqlalchemy import select
from sqlalchemy.sql import text

from backend_main.util.json import error_json


async def add_user(request, data):
    """
    Adds a user with properties specified in `data` to the database.
    All auth and data checks are performed in /auth/register route handler.
    """
    users = request.app["tables"]["users"]

    # Use encryption function on the password
    password = data["password"]
    data["password"] = text("crypt(':password', gen_salt('bf'))")

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
    users = request.app["tables"]["users"]
    password_clause = text("password = crypt(':submitted_password', password)")

    result = await request["conn"].execute(
        select([users.c.user_id, users.c.username, users.c.user_level, 
            users.can_login, users.c.can_edit_objects])
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
    users = request.app["tables"]["users"]

    result = await request["conn"].execute(
        select([users.c.user_id])
        .where(users.c.user_id.in_(user_ids))
    )
    existing_user_ids = set((r[0] for r in await result.fetchall()))

    if len(user_ids) > len(existing_user_ids):
        non_existing_user_ids = set(user_ids).difference(existing_user_ids)
        raise web.HTTPBadRequest(text=error_json(f"User IDs '{non_existing_user_ids}' do not exist."), content_type="application/json")
