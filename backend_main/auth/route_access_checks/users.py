"""
Middleware auth checks for /users/* routes.
"""
from backend_main.auth.route_access_checks.util import debounce_anonymous


def users_update(request):
    """
    - if unauthenticated or invalid token, return 401;
    """
    debounce_anonymous(request)


users_checks = {
    "/users/update": users_update
}
