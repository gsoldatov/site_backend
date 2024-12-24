"""
Middleware auth checks for /objects/* routes.
"""
from backend_main.auth.route_access.common import forbid_anonymous, forbid_authenticated_non_admins_who_cant_edit

from backend_main.types.request import Request


def objects_modify(request: Request):
    """
    - if unauthenticated or invalid token, return 401;
    - if not an admin & `can_edit_objects` = false, return 403;
    """
    forbid_anonymous(request)
    forbid_authenticated_non_admins_who_cant_edit(request)


objects_checks = {
    "/objects/add": objects_modify,
    "/objects/update": objects_modify,
    "/objects/delete": objects_modify,
    "/objects/update_tags": objects_modify
}
