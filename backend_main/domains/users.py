from backend_main.db_operations2.users import \
    add_user as _add_user, \
    update_user as _update_user, \
    get_user_by_login_and_password as _get_user_by_login_and_password, \
    get_user_by_id_and_password as _get_user_by_id_and_password, \
    view_users as _view_users

from backend_main.types.domains.users import User, NewUser, UserFull, UserMin, UserUpdate
from backend_main.types.request import Request


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
