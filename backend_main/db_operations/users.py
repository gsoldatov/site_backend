"""
User-related database operations.
"""
from aiohttp import web
from sqlalchemy import select

from backend_main.util.json import error_json

from backend_main.types.app import app_tables_key
from backend_main.types.request import request_log_event_key, request_connection_key


async def check_if_user_ids_exist(request, user_ids):
    """
    Checks if provided `user_id` exists in the database.
    Raises 400 if not.
    """
    if len(user_ids) == 0: return
    users = request.config_dict[app_tables_key].users

    result = await request[request_connection_key].execute(
        select(users.c.user_id)
        .where(users.c.user_id.in_(user_ids))
    )
    existing_user_ids = set((r[0] for r in await result.fetchall()))

    if len(user_ids) > len(existing_user_ids):
        non_existing_user_ids = set(user_ids).difference(existing_user_ids)
        msg = "Users do not exist."
        request[request_log_event_key]("WARNING", "db_operation", msg, details=f"user_ids = {non_existing_user_ids}")
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")
