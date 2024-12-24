"""
Middleware auth checks for /tags/* routes.
"""
from backend_main.auth.route_access.common import forbid_anonymous, forbid_authenticated_non_admins

from backend_main.types.request import Request


def tags_modify(request: Request):
    """
    - if unauthenticated or invalid token, return 401;
    - if not an admin, return 403;
    """
    forbid_anonymous(request)
    forbid_authenticated_non_admins(request)


tags_checks = {
    "/tags/add": tags_modify,
    "/tags/update": tags_modify,
    "/tags/delete": tags_modify
}
