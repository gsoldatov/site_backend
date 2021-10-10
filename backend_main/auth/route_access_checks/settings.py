"""
Middleware auth checks for /settings/* routes.
"""
from backend_main.auth.route_access_checks.util import debounce_anonymous, debounce_authenticated_non_admins


def settings_update(request):
    """
    - if unauthenticated or invalid token, return 401;
    - if authenticated non-admin, return 403;
    """
    debounce_anonymous(request)
    debounce_authenticated_non_admins(request)


settings_checks = {
    "/settings/update": settings_update
}
