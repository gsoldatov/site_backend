"""
/users/... route auth checks, which rely on request data.
"""
from aiohttp import web
from typing import cast

from backend_main.auth.route_access.common import forbid_anonymous

from backend_main.domains.users import get_user_by_id_and_password

from backend_main.util.constants import forbidden_non_admin_user_modify_attributes
from backend_main.util.json import error_json

from backend_main.types.domains.users import UserUpdate
from backend_main.types.routes.users import UsersUpdateRequestBody, UsersViewRequestBody
from backend_main.types.request import Request, request_log_event_key, request_user_info_key


def authorize_user_update(request: Request, user_update: UserUpdate) -> None:
    """
    Checks if non-admin does not update another user or its own privileges.
    """
    if request[request_user_info_key].user_level == "admin": return
    
    if request[request_user_info_key].user_id != user_update.user_id:
        msg = "Attempted to edit another user as a non-admin."
        request[request_log_event_key]("WARNING", "auth", msg)
        raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
    
    for attr in forbidden_non_admin_user_modify_attributes:
        if getattr(user_update, attr, None) is not None:
            msg = "Attempted to set user privilege as a non-admin."
            request[request_log_event_key]("WARNING", "auth", msg)
            raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")


async def validate_user_update_issuer(request: Request, request_data: UsersUpdateRequestBody) -> None:
    """
    Checks if user update issuer provided correct password.
    """
    token_owner_user_id = cast(int, request[request_user_info_key].user_id)
    user = await get_user_by_id_and_password(request, token_owner_user_id, request_data.token_owner_password)
    
    if user is None:
        msg = "Password is incorrect."
        request[request_log_event_key]("WARNING", "auth", msg)
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")


def authorize_users_view(request: Request, request_data: UsersViewRequestBody) -> None:
    """
    Checks if non-admin does not view full user data of other users.
    """
    if request_data.full_view_mode:
        forbid_anonymous(request)
        
        if request[request_user_info_key].user_level != "admin":
            if len(request_data.user_ids) > 1 or request_data.user_ids[0] != request[request_user_info_key].user_id:
                msg = "Attempted to view full information about other users as a non-admin."
                request[request_log_event_key]("WARNING", "auth", msg)
                raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
