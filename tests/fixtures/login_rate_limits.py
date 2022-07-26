from datetime import datetime, timedelta

from psycopg2.extensions import AsIs


def get_test_login_rate_limit(ip_address, failed_login_attempts = None, cant_login_until = None, pop_keys = []):
    """
    Returns a new dictionary for `login_rate_limits` table with attributes specified in `pop_keys` popped from it.
    `ip_address` value is provided as the first arguments, other attributes can be optionally provided to override default values.
    """
    failed_login_attempts = failed_login_attempts if failed_login_attempts is not None else 5
    cant_login_until = cant_login_until if cant_login_until is not None else datetime.utcnow() + timedelta(seconds=60)

    login_rate_limit = {"ip_address": ip_address, "failed_login_attempts": failed_login_attempts, "cant_login_until": cant_login_until}
    for k in pop_keys:
        login_rate_limit.pop(k, None)
    return login_rate_limit


def insert_login_rate_limits(login_rate_limits, db_cursor):
    """
    Inserts a list of `login_rate_limits` into login_rate_limits table.
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s)" for _ in range(len(login_rate_limits))))
    params = [AsIs("login_rate_limits")]
    for t in login_rate_limits:
        params.extend(t.values())
    db_cursor.execute(query, params)
