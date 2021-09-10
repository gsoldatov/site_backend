def get_login_attempts_timeout_in_seconds(failed_login_attempts):
    """
    Returns the number of seconds before the next possible login attempt for the provided `failed_login_attempts` number.
    Number of seconds is negative for the first attempts.
    """
    return _LOGIN_TIMEOUTS[failed_login_attempts] if failed_login_attempts < len(_LOGIN_TIMEOUTS) else 3600


_LOGIN_TIMEOUTS = [-60] * 10
_LOGIN_TIMEOUTS.extend([5, 10, 20, 30, 60, 120, 600, 1200, 1800, 3600])
