class IncorrectCredentialsException(Exception):
    """
    Exception thrown when a login attempts has failed.
    Required to commit login_rate_limits into the database.
    """
    pass


def get_login_attempts_timeout_in_seconds(failed_login_attempts):
    """
    Returns the number of seconds before the next possible login attempt for the provided `failed_login_attempts` number.
    Number of seconds is negative for the first attempts.
    """
    return _LOGIN_TIMEOUTS[failed_login_attempts] if failed_login_attempts < len(_LOGIN_TIMEOUTS) else _LOGIN_TIMEOUT_DEFAULT


_LOGIN_TIMEOUTS = [-60] * 9
_LOGIN_TIMEOUTS.extend([5, 10, 20, 30, 60, 120, 600, 1200, 1800])

_LOGIN_TIMEOUT_DEFAULT = 3600
