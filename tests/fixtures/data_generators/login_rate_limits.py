from datetime import datetime, timezone, timedelta


def get_test_login_rate_limit(ip_address, failed_login_attempts = None, cant_login_until = None, pop_keys = []):
    """
    Returns a new dictionary for `login_rate_limits` table with attributes specified in `pop_keys` popped from it.
    `ip_address` value is provided as the first arguments, other attributes can be optionally provided to override default values.
    """
    failed_login_attempts = failed_login_attempts if failed_login_attempts is not None else 5
    cant_login_until = cant_login_until if cant_login_until is not None else datetime.now(tz=timezone.utc) + timedelta(seconds=60)

    login_rate_limit = {"ip_address": ip_address, "failed_login_attempts": failed_login_attempts, "cant_login_until": cant_login_until}
    for k in pop_keys:
        login_rate_limit.pop(k, None)
    return login_rate_limit