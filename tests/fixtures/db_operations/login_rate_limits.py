from psycopg2.extensions import AsIs


def insert_login_rate_limits(login_rate_limits, db_cursor):
    """
    Inserts a list of `login_rate_limits` into login_rate_limits table.
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s)" for _ in range(len(login_rate_limits))))
    params = [AsIs("login_rate_limits")]
    for t in login_rate_limits:
        params.extend(t.values())
    db_cursor.execute(query, params)
