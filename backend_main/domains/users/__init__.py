from aiohttp import web

from backend_main.auth.route_access.common import forbid_anonymous

from backend_main.db_operations2.users import add_user as _add_user, \
    get_user_by_login_and_password as _get_user_by_login_and_password, \
    view_users as _view_users

from backend_main.util.exceptions import UserFullViewModeNotAllowed

from backend_main.types.domains.users import User, NewUser, UserFull, UserMin
from backend_main.types.request import Request, request_user_info_key


async def add_user(request: Request, new_user: NewUser) -> User:
    return await _add_user(request, new_user)


async def get_user_by_login_and_password(request: Request, login: str, password: str) -> User | None:
    return await _get_user_by_login_and_password(request, login, password)


async def view_users(request: Request, user_ids: list[int], full_view_mode: bool) -> list[UserFull] | list[UserMin]:
    # Check if operation is authorized
    if full_view_mode:
        forbid_anonymous(request)
        
        if request[request_user_info_key].user_level != "admin":
            if len(user_ids) > 1 or user_ids[0] != request[request_user_info_key].user_id:
                raise UserFullViewModeNotAllowed()

    # Query data
    return await _view_users(request, user_ids, full_view_mode)
