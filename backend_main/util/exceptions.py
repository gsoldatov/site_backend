class InvalidNewUserAttributesException(Exception):
    """
    Raised when new user data contains unallowed attributes,
    e.g., when a non-admin tries to set user privileges.
    """
    pass


class IncorrectCredentialsException(Exception):
    """
    Raised when a login attempts has failed.
    Required to commit login_rate_limits into the database.
    """
    pass


class UserFullViewModeNotAllowed(Exception):
    """
    Raised when full data of another user is requested by a non-admin.
    """
    pass
