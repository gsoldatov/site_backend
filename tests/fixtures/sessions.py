from datetime import datetime, timedelta
from uuid import uuid4

from psycopg2.extensions import AsIs


admin_token = "admin token"
non_existing_token = "non-existing token"

headers_admin_token = {"Authorization": f"Bearer {admin_token}"}
headers_non_existing_token = {"Authorization": f"Bearer {non_existing_token}"}


def get_test_session(user_id, access_token = None, expiration_time = None, pop_keys = []):
    """
    Returns a new dictionary for `sessions` table with attributes specified in `pop_keys` popped from it.
    `user_id` value is provided as the first arguments, other attributes can be optionally provided to override default values.
    """
    access_token = access_token if access_token is not None else generate_random_token()
    expiration_time = expiration_time if expiration_time is not None else datetime.utcnow() + timedelta(seconds=60)

    session = {"user_id": user_id, "access_token": access_token, "expiration_time": expiration_time}
    for k in pop_keys:
        session.pop(k, None)
    return session

generate_random_token = lambda: uuid4().hex


def insert_sessions(sessions, db_cursor):
    """
    Inserts a list of `sessions` into sessions table.
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s)" for _ in range(len(sessions))))
    params = [AsIs("sessions")]
    for t in sessions:
        params.extend(t.values())
    db_cursor.execute(query, params)
