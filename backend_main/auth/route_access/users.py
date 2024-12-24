"""
Middleware auth checks for /users/* routes.
"""
from backend_main.auth.route_access.common import forbid_anonymous

from backend_main.types.request import Request


def users_update(request: Request):
    """
    - if unauthenticated or invalid token, return 401;
    """
    forbid_anonymous(request)


users_checks = {
    "/users/update": users_update
}
