"""
Middleware auth checks for /auth/* routes.
"""
from backend_main.auth.route_access_checks.util import debounce_anonymous, \
    debounce_authenticated_non_admins, debounce_authenticated

from backend_main.util.constants import AUTH_SUBAPP_PREFIX


def register(request):
    """
    - if authenticated & not an admin, return 403;
    """
    debounce_authenticated_non_admins(request)


def login(request):
    """
    - if authenticated or can't login, return 403;
    """
    debounce_authenticated(request)


def logout(request):
    """
    - if anonymous, return 401;
    """
    debounce_anonymous(request)

auth_checks = {
    f"/{AUTH_SUBAPP_PREFIX}/register": register,
    f"/{AUTH_SUBAPP_PREFIX}/login": login,
    f"/{AUTH_SUBAPP_PREFIX}/logout": logout
}
