"""
Session-related database operations.
"""
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select, and_

from backend_main.types.app import app_config_key, app_tables_key
from backend_main.types.domains.sessions import Session
from backend_main.types.request import Request, UserInfo, request_time_key, request_connection_key


async def add_session(request: Request, user_id: int) -> Session:
    """
    Adds a new session for the provided `user_id` and returns the generated access token.
    """
    sessions = request.config_dict[app_tables_key].sessions
    request_time = request[request_time_key]
    
    session = Session(
        user_id=user_id,
        access_token=uuid4().hex,
        expiration_time=request_time + timedelta(seconds=request.config_dict[app_config_key].app.token_lifetime)
    )

    await request[request_connection_key].execute(
        sessions.insert()
        .values(session.model_dump())
    )

    return session


async def prolong_access_token_and_get_user_info(
        request: Request,
        access_token: str
    ) -> UserInfo | None:
    """
    Prolongs `access_token` duration and returns `UserInfo` for valid tokens.
    Returns `None`, if `access_token` is invalid, expired or belongs to a user, who can't login.
    """
    users = request.config_dict[app_tables_key].users
    sessions = request.config_dict[app_tables_key].sessions
    request_time = request[request_time_key]
    expiration_time = request_time + timedelta(seconds=request.config_dict[app_config_key].app.token_lifetime)

    # Update expiration time and return user information corresponding to the updated token 
    # in a single query using CTE.
    # NOTE: values updated in CTE can't be fetched with select in the same query.
    update_cte = (
        sessions.update()
        .where(and_(
            sessions.c.access_token == access_token,
            sessions.c.expiration_time > request_time
        ))
        .values({"expiration_time": expiration_time})
        .returning(sessions.c.user_id.label("user_id"))
    ).cte("update_cte")

    result = await request[request_connection_key].execute(
        select(
            users.c.user_id,
            users.c.user_level,
            users.c.can_edit_objects
        ).where(and_(
            users.c.user_id.in_(select(update_cte.c.user_id)),
            users.c.can_login == True
        ))
    )

    row = await result.fetchone()

    if row is None:
        return None
    else:
        return UserInfo(
            access_token=access_token,
            user_id=row[0],
            user_level=row[1],
            can_edit_objects=row[2],
            access_token_expiration_time=expiration_time
        )


async def delete_sessions_by_access_tokens(request: Request, access_tokens: list[str]) -> None:
    """
    Deletes sessions for with specified `access_tokens`.
    """
    sessions = request.config_dict[app_tables_key].sessions

    await request[request_connection_key].execute(
        sessions.delete()
        .where(sessions.c.access_token.in_(access_tokens))
    )


async def delete_sessions_by_user_ids(request: Request, user_ids: list[int]) -> None:
    """
    Deletes sessions of users with specified `user_ids`.
    """
    sessions = request.config_dict[app_tables_key].sessions

    await request[request_connection_key].execute(
        sessions.delete()
        .where(sessions.c.user_id.in_(user_ids))
    )
