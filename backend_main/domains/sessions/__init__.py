from backend_main.db_operations2.sessions import add_session as _add_session, \
    delete_sessions_by_access_tokens as _delete_sessions_by_access_tokens, \
    delete_sessions_by_user_ids as _delete_sessions_by_user_ids

from backend_main.types.domains.sessions import Session
from backend_main.types.request import Request


async def add_session(request: Request, user_id: int) -> Session:
    return await _add_session(request, user_id)


async def delete_session_by_access_token(request: Request, access_token: str | None) -> None:
    if access_token is not None:
        return await _delete_sessions_by_access_tokens(request, [access_token])


async def delete_user_sessions(request: Request, user_id: int) -> None:
    return await _delete_sessions_by_user_ids(request, [user_id])
