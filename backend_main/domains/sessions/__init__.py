from backend_main.db_operations2.sessions import add_session as _add_session

from backend_main.types.domains.sessions import Session
from backend_main.types.request import Request


async def add_session(request: Request, user_id: int) -> Session:
    return await _add_session(request, user_id)
