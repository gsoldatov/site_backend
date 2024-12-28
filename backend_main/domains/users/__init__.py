from aiohttp import web

from backend_main.auth.route_access.common import forbid_anonymous

from backend_main.db_operations2.users import add_user as _add_user, \
    update_user as _update_user, \
    get_user_by_login_and_password as _get_user_by_login_and_password, \
    get_user_by_id_and_password as _get_user_by_id_and_password, \
    view_users as _view_users

from backend_main.util.constants import forbidden_non_admin_user_modify_attributes
from backend_main.util.exceptions import UserFullViewModeNotAllowed
from backend_main.util.json import error_json

from backend_main.types.domains.users import User, NewUser, UserFull, UserMin, UserUpdate
from backend_main.types.request import Request, request_user_info_key, request_log_event_key


async def add_user(request: Request, new_user: NewUser) -> User:
    return await _add_user(request, new_user)


def validate_user_update(request: Request, user_update: UserUpdate) -> None:
    # TODO move to auth checks
    if request[request_user_info_key].user_level != "admin":
        if request[request_user_info_key].user_id != user_update.user_id:
            msg = "Attempted to edit another user as a non-admin."
            request[request_log_event_key]("WARNING", "db_operation", msg)
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
        
        for attr in forbidden_non_admin_user_modify_attributes:
            if getattr(user_update, attr, None) is not None:
                msg = "Attempted to set user privilege as a non-admin."
                request[request_log_event_key]("WARNING", "db_operation", msg)
                raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


async def update_user(request: Request, user_update: UserUpdate) -> int | None:
    return await _update_user(request, user_update)


async def get_user_by_login_and_password(request: Request, login: str, password: str) -> User | None:
    return await _get_user_by_login_and_password(request, login, password)


async def check_password_for_user_id(request: Request, user_id: int, password: str) -> None:
    # TODO move to auth checks
    if await _get_user_by_id_and_password(request, user_id, password) is None:
        msg = "Password is incorrect."
        request[request_log_event_key]("WARNING", "db_operation", msg)
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")


async def view_users(request: Request, user_ids: list[int], full_view_mode: bool) -> list[UserFull] | list[UserMin]:
    # Check if operation is authorized
    # TODO move to auth checks
    if full_view_mode:
        forbid_anonymous(request)
        
        if request[request_user_info_key].user_level != "admin":
            if len(user_ids) > 1 or user_ids[0] != request[request_user_info_key].user_id:
                raise UserFullViewModeNotAllowed()

    # Query data
    return await _view_users(request, user_ids, full_view_mode)
