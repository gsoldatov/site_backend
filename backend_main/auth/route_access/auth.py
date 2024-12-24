"""
Middleware auth checks for /auth/* routes.
"""
from backend_main.auth.route_access.common import forbid_anonymous, \
    forbid_authenticated_non_admins, forbid_authenticated

from backend_main.util.constants import AUTH_SUBAPP_PREFIX

from backend_main.types.request import Request


def register(request: Request):
    """
    - if authenticated & not an admin, return 403;
    """
    forbid_authenticated_non_admins(request)


def login(request: Request):
    """
    - if authenticated or can't login, return 403;
    """
    forbid_authenticated(request)


def logout(request: Request):
    """
    - if anonymous, return 401;
    """
    forbid_anonymous(request)

auth_checks = {
    f"/{AUTH_SUBAPP_PREFIX}/register": register,
    f"/{AUTH_SUBAPP_PREFIX}/login": login,
    f"/{AUTH_SUBAPP_PREFIX}/logout": logout
}
