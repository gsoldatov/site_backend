"""
Session-related database operations.
"""
from datetime import datetime, timedelta
from uuid import uuid4

from aiohttp import web
from sqlalchemy import select, and_

from backend_main.util.constants import ROUTES_WITHOUT_INVALID_TOKEN_DEBOUNCING
from backend_main.util.json import error_json


async def prolong_access_token_and_get_user_info(request):
    """
    Gets user information for the provided access token and adds it to `request.user_info`.
    Raises 401 if token is not found or expired, or is user's `can_login` attribute is false.
    Prolongs the lifetime of the token if otherwise.
    """
    # Exit if anonymous
    if request.user_info.is_anonymous: return
    
    users = request.app["tables"]["users"]
    sessions = request.app["tables"]["sessions"]
    current_time = datetime.utcnow()
    expiration_time = current_time + timedelta(seconds=request.config_dict["config"]["app"]["token_lifetime"])

    # Update expiration time and return user information corresponding to the updated token 
    # in a single query using CTE.
    # NOTE: values updated in CTE can't be fetched with select in the same query.
    update_cte = (
        sessions.update()
        .where(and_(
            sessions.c.access_token == request.user_info.access_token,
            sessions.c.expiration_time > current_time
        ))
        .values({"expiration_time": expiration_time})
        .returning(sessions.c.user_id.label("user_id"))
    ).cte("update_cte")

    result = await request["conn"].execute(
        select([users.c.user_id, users.c.user_level, users.c.can_edit_objects])
        .where(and_(
            users.c.user_id.in_(select([update_cte.c.user_id])),
            users.c.can_login == True
        ))
    )

    info = await result.fetchone()

    # Raise 401 if token was not found or expired, os user is not allowed to login
    if not info:
        # Don't raise for some route
        if request.path not in ROUTES_WITHOUT_INVALID_TOKEN_DEBOUNCING:
            raise web.HTTPUnauthorized(text=error_json("Invalid token."), content_type="application/json")
    else:
        ui = request.user_info
        ui.user_id, ui.user_level, ui.can_edit_objects = info[0], info[1], info[2]
        ui.access_token_expiration_time = expiration_time


async def add_session(request, user_id):
    """
    Adds a new session for the provided `user_id` and returns the generated access token.
    """
    sessions = request.app["tables"]["sessions"]
    
    data = {
        "user_id": user_id,
        "access_token": uuid4().hex,
        "expiration_time": datetime.utcnow() + timedelta(seconds=request.config_dict["config"]["app"]["token_lifetime"])
    }

    await request["conn"].execute(
        sessions.insert()
        .values(data)
    )

    return data


async def delete_sessions(request, access_tokens):
    """
    Deletes sessions with specified `access_tokens`.
    """
    sessions = request.app["tables"]["sessions"]

    await request["conn"].execute(
        sessions.delete()
        .where(sessions.c.access_token.in_(access_tokens))
    )
