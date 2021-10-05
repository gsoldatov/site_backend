"""
Middleware auth checks for /objects/* routes.
"""
from backend_main.auth.route_access_checks.util import debounce_anonymous, debounce_authenticated_non_admins_who_cant_edit


def objects_modify(request):
    """
    - if unauthenticated or invalid token, return 401;
    - if not an admin & `can_edit_objects` = false, return 403;
    """
    debounce_anonymous(request)
    debounce_authenticated_non_admins_who_cant_edit(request)


objects_checks = {
    "/objects/add": objects_modify,
    "/objects/update": objects_modify,
    "/objects/delete": objects_modify,
    "/objects/update_tags": objects_modify
}
