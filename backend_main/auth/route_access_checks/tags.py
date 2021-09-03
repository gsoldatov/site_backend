"""
Auth checks for /tags/* routes.
"""
from backend_main.auth.route_access_checks.util import debounce_anonymous, debounce_authenticated_non_admins


def tags_modify(request):
    """
    - if unauthorized or invalid token, return 401;
    - if not an admin, return 403;
    """
    debounce_anonymous(request)
    debounce_authenticated_non_admins(request)


tags_checks = {
    "/tags/add": tags_modify,
    "/tags/update": tags_modify,
    "/tags/delete": tags_modify
}
