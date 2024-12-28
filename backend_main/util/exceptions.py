class IncorrectCredentialsException(Exception):
    """
    Raised when a login attempts has failed.
    Required to commit login_rate_limits into the database.
    """
    pass
