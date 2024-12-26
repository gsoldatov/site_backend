"""
User-related database operations.
"""
from aiohttp import web
from sqlalchemy import select, and_
from sqlalchemy.sql import text

from backend_main.auth.route_access.common import forbid_anonymous

from backend_main.db_operations.sessions import delete_sessions

from backend_main.middlewares.connection import start_transaction

from backend_main.util.constants import forbidden_non_admin_user_modify_attributes
from backend_main.util.json import error_json

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.users import NewUser, User


async def add_user(request: Request, new_user: NewUser) -> User:
    """ Adds a `new_user` to the database. """
    users = request.config_dict[app_tables_key].users

    # Use encryption function on the password
    values = new_user.model_dump()
    values["password"] = text("crypt(:password, gen_salt('bf'))")

    result = await request[request_connection_key].execute(
        users.insert()
        .returning(
            users.c.user_id,
            users.c.login,
            users.c.username,
            users.c.registered_at,
            users.c.user_level,
            users.c.can_login,
            users.c.can_edit_objects
        ).values(values)
    , password=new_user.password)    # password is passed as a bind parameter in order to escape it
    
    return User(**(await result.fetchone()))
