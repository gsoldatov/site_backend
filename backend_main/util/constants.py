AUTH_SUBAPP_PREFIX = "auth"

ROUTES_WITHOUT_INVALID_TOKEN_DEBOUNCING = set((
    "/auth/logout",
    "/settings/view"
))

forbidden_non_admin_user_modify_attributes = ("user_level", "can_login", "can_edit_objects")
