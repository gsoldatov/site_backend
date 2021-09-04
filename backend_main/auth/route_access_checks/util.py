"""
Common auth checks for route handlers.
"""
from aiohttp import web

from backend_main.util.json import error_json


def debounce_anonymous(request):
    """
    Raises 401 if user is anonymous.
    """
    if request.user_info.is_anonymous:
        raise web.HTTPUnauthorized(text=error_json("Authentication required."), content_type="application/json")


def debounce_authenticated_non_admins(request):
    """
    Raises 403 if user is not anonymous and 'user_level' != 'admin'.
    """
    if not request.user_info.is_anonymous and request.user_info.user_level != "admin":
        raise web.HTTPForbidden(text=error_json("Operation forbidden."), content_type="application/json")


def debounce_authenticated_non_admins_who_cant_edit(request):
    """
    Raises 403 if user is not anonymouse, 'user_level' != 'admin' and `can_edit_objects` = false.
    """
    if not request.user_info.is_anonymous and request.user_info.user_level != "admin" and not request.user_info.can_edit_objects:
        raise web.HTTPForbidden(text=error_json("Operation forbidden."), content_type="application/json")


def debounce_non_admin_changing_object_owner(request, objects_attributes, is_objects_update = False):
    """
    Raises 403 if 'user_level' != admin and one or more of the added/updated objects in `objects_attributes` have their `owner_id` explicitly set.
    
    If `is_objects_update` is true, allows `owner_id` to be not present in the objects' attributes.
    Otherwise, `owner_id_is_autoset` and `owner_id` attributes are expected in every object.
    """
    if request.user_info.user_level != "admin":
        # Check for `add_objects` operation
        if not is_objects_update:
            for o in objects_attributes:
                if not o["owner_id_is_autoset"] and o["owner_id"] != request.user_info.user_id:
                    raise web.HTTPForbidden(text=error_json("Users are not allowed to change object owners."), content_type="application/json")
        
        # Check for `update_objects` operation
        else:
            for o in objects_attributes:
                if "owner_id" in o:
                    if o["owner_id"] != request.user_info.user_id:
                        raise web.HTTPForbidden(text=error_json("Users are not allowed to change object owners."), content_type="application/json")

