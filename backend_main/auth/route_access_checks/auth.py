"""
Auth checks for /auth/* routes.
"""
from backend_main.auth.route_access_checks.util import debounce_anonymous, \
    debounce_authenticated_non_admins, debounce_authenticated


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
    - if anonymous, return 403;
    """
    debounce_anonymous(request)

auth_checks = {
    "/auth/register": register,
    "/auth/login": login,
    "/auth/logout": logout
}
