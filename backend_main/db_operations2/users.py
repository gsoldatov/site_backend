"""
User-related database operations.
"""
from sqlalchemy import select, and_
from sqlalchemy.sql import text

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.users import NewUser, User, UserFull, UserMin, UserUpdate


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


async def update_user(request: Request, user_update: UserUpdate) -> int | None:
    """
    Updates an existing user with properties specified from `user_update`.
    """
    users = request.config_dict[app_tables_key].users
    values = user_update.model_dump(exclude_none=True, exclude={"user_id", "password"})
    if user_update.password is not None:
        values["password"] = text("crypt(:password, gen_salt('bf'))")
    
    result = await request[request_connection_key].execute(
        users.update()
        .where(users.c.user_id == user_update.user_id)
        .values(values)
        .returning(users.c.user_id)
    , password=user_update.password)    # password is passed as a bind parameter in order to escape it

    # Handle user not found case
    if not await result.fetchone(): return None

    # Return user ID if successfully updated
    return user_update.user_id


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


async def get_user_by_id_and_password(request: Request, user_id: int, password: str) -> User | None:
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


async def view_users(request: Request, user_ids: list[int], full_view_mode: bool) -> list[UserFull] | list[UserMin]:
    """
    Returns public user attributes for the users with provided `user_ids`.
    If `full_view_mode` is true, returns full information about user, otherwise - only `username` and `registered_at`.
    """
    users = request.config_dict[app_tables_key].users
    
    result = await request[request_connection_key].execute(
        select(
            users.c.user_id,
            users.c.username,
            users.c.registered_at,
            users.c.user_level,
            users.c.can_login,
            users.c.can_edit_objects
        )
        .where(users.c.user_id.in_(user_ids))
    )

    if full_view_mode:
        return [UserFull.model_validate(row) for row in await result.fetchall()]
    else:
        return [UserMin.model_validate(row) for row in await result.fetchall()]
