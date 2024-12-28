AUTH_SUBAPP_PREFIX = "auth"

ROUTES_ACCESSIBLE_WITH_INVALID_ACCESS_TOKEN = set((
    "/auth/logout",
    "/settings/view"
))

USER_PRIVILEGE_ATTRIBUTES = ("user_level", "can_login", "can_edit_objects")
