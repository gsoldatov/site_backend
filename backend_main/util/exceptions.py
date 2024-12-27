class InvalidNewUserAttributesException(Exception):
    """
    Exception thrown when new user data contains unallowed attributes,
    e.g., when a non-admin tries to set user privileges.
    """
    pass


class IncorrectCredentialsException(Exception):
    """
    Exception thrown when a login attempts has failed.
    Required to commit login_rate_limits into the database.
    """
    pass