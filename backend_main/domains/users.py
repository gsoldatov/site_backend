from aiohttp import web
from typing import Iterable

from backend_main.db_operations.users import \
    add_user as _add_user, \
    update_user as _update_user, \
    get_user_by_login_and_password as _get_user_by_login_and_password, \
    get_user_by_id_and_password as _get_user_by_id_and_password, \
    view_users as _view_users, \
    get_existing_user_ids as _get_existing_user_ids

from backend_main.util.json import error_json

from backend_main.types.domains.users import User, NewUser, UserFull, UserMin, UserUpdate
from backend_main.types.request import Request, request_log_event_key


async def add_user(request: Request, new_user: NewUser) -> User:
    return await _add_user(request, new_user)


async def update_user(request: Request, user_update: UserUpdate) -> int | None:
    return await _update_user(request, user_update)


async def get_user_by_login_and_password(request: Request, login: str, password: str) -> User | None:
    return await _get_user_by_login_and_password(request, login, password)


async def get_user_by_id_and_password(request: Request, user_id: int, password: str) -> User | None:
    return await _get_user_by_id_and_password(request, user_id, password)


async def view_users(request: Request, user_ids: list[int], full_view_mode: bool) -> list[UserFull] | list[UserMin]:
    return await _view_users(request, user_ids, full_view_mode)


async def ensure_user_ids_exist(request: Request, user_ids: Iterable[int]) -> None:
    """
    Checks if provided `user_id` exists in the database.
    Raises 400 if not.
    """
    user_ids_set = set(user_ids)
    if len(user_ids_set) == 0: return
    
    existing_user_ids = await _get_existing_user_ids(request, user_ids_set)

    if len(user_ids_set) > len(existing_user_ids):
        non_existing_user_ids = list(user_ids_set.difference(existing_user_ids))
        msg = "Users do not exist."
        request[request_log_event_key]("WARNING", "domain", msg, details={"user_ids": non_existing_user_ids})
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")
