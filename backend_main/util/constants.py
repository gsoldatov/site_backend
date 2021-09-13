AUTH_SUBAPP_PREFIX = "auth"

ROUTES_WITHOUT_INVALID_TOKEN_DEBOUNCING = set((
    "/auth/logout",
    "/auth/get_registration_status"
))