"""
User-related database operations.
"""
from sqlalchemy import select, and_
from sqlalchemy.sql import text

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


async def get_user_by_login_and_password(request: Request, login: str, password: str) -> User | None:
    """
    Returns information about the user with provided `login` and `password`, if he exists.
    """
    # Exit if argument values are incorrect
    if len(password) < 8 or len(password) > 72: return None
    
    users = request.config_dict[app_tables_key].users
    password_clause = text("password = crypt(:submitted_password, password)")

    result = await request[request_connection_key].execute(
        select(
            users.c.user_id,
            users.c.login,
            users.c.username,
            users.c.registered_at,
            users.c.user_level,
            users.c.can_login,
            users.c.can_edit_objects
        ).where(and_(
            users.c.login == login,
            password_clause
        ))
    , submitted_password=password)  # password is passed as a bind parameter in order to escape it

    row = await result.fetchone()

    return User(**row) if row is not None else None


async def get_user_by_id_and_password(request: Request, user_id: str, password: str) -> User | None:
    """
    Returns information about the user with provided `user_id` and `password`, if he exists.
    """
    # Exit if argument values are incorrect
    if len(password) < 8 or len(password) > 72: return None
    
    users = request.config_dict[app_tables_key].users
    password_clause = text("password = crypt(:submitted_password, password)")

    result = await request[request_connection_key].execute(
        select(
            users.c.user_id,
            users.c.login,
            users.c.username,
            users.c.registered_at,
            users.c.user_level,
            users.c.can_login,
            users.c.can_edit_objects
        ).where(and_(
            users.c.user_id == user_id,
            password_clause
        ))
    , submitted_password=password)  # password is passed as a bind parameter in order to escape it

    row = await result.fetchone()

    return User(**row) if row is not None else None
