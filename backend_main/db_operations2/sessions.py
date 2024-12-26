"""
Session-related database operations.
"""
from datetime import timedelta
from uuid import uuid4

from aiohttp import web
from sqlalchemy import select, and_

from backend_main.util.constants import ROUTES_WITHOUT_INVALID_TOKEN_DEBOUNCING
from backend_main.util.json import error_json

from backend_main.types.app import app_config_key, app_tables_key
from backend_main.types.domains.sessions import Session
from backend_main.types.request import Request, request_time_key, request_user_info_key, request_connection_key


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
