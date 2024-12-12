from psycopg2.extensions import AsIs


def insert_sessions(sessions, db_cursor):
    """
    Inserts a list of `sessions` into sessions table.
    """
    # query
    field_order = ["user_id", "access_token", "expiration_time"]
    fields_tuple = "(" + ", ".join(field_order) + ")"
    query = f"INSERT INTO %s {fields_tuple} VALUES " + ", ".join(("(%s, %s, %s)" for _ in range(len(sessions))))
    
    # params
    table = "sessions"
    params = [AsIs(table)]
    for u in sessions:
        for f in field_order:
            params.append(u[f])

    db_cursor.execute(query, params)
