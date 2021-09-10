"""
Auth middleware checks for specific app routes.
"""
from backend_main.auth.route_access_checks.objects import objects_checks
from backend_main.auth.route_access_checks.tags import tags_checks
from backend_main.auth.route_access_checks.auth import auth_checks


def check_route_access(request):
    """
    Checks if the requested route can be accessed with provided access token.
    """
    for checks in (objects_checks, tags_checks, auth_checks):
        check = checks.get(request.path)
        if check:
            check(request)
            break
