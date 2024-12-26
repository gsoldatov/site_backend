from aiohttp import web

from backend_main.db_operations2.users import add_user as add_user_db_op

from backend_main.util.constants import forbidden_non_admin_user_modify_attributes
from backend_main.util.json import error_json

from backend_main.types.routes.auth import AuthRegisterRequestBody
from backend_main.types.domains.users import User, NewUser
from backend_main.types.request import Request, request_user_info_key, request_log_event_key, \
    request_time_key


async def add_user(request: Request, new_user: NewUser) -> User:
    return await add_user_db_op(request, new_user)
