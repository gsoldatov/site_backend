"""
Middleware auth checks for /settings/* routes.
"""
from backend_main.auth.route_access.common import forbid_anonymous, forbid_authenticated_non_admins

from backend_main.types.request import Request


def settings_update(request: Request):
    """
    - if unauthenticated or invalid token, return 401;
    - if authenticated non-admin, return 403;
    """
    forbid_anonymous(request)
    forbid_authenticated_non_admins(request)


settings_checks = {
    "/settings/update": settings_update
}
