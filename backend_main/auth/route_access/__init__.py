"""
Auth middleware checks for specific app routes.
"""
from backend_main.auth.route_access.objects import objects_checks
from backend_main.auth.route_access.tags import tags_checks
from backend_main.auth.route_access.auth import auth_checks
from backend_main.auth.route_access.settings import settings_checks
from backend_main.auth.route_access.users import users_checks

from backend_main.types.request import Request


def authorize_route_access(request: Request):
    """
    Checks if the requested route can be accessed with provided access token.
    """
    for checks in (objects_checks, tags_checks, auth_checks, settings_checks, users_checks):
        check = checks.get(request.path)
        if check:
            check(request)
            break
