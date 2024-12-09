from datetime import datetime, timezone, timedelta

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.sessions import headers_admin_token
from tests.fixtures.users import get_test_user, insert_users, incorrect_user_attributes


async def test_incorrect_request_body(cli, db_cursor):
    # Insert a user
    user = get_test_user(2, pop_keys=["password_repeat"])
    insert_users([user], db_cursor)

    # Incorrect request body
    resp = await cli.post("/auth/login", data="not a JSON document.")
    assert resp.status == 400

    # Required attributes missing
    for attr in ("login", "password"):
        credentials = {"login": user["login"], "password": user["password"]}
        credentials.pop(attr)
        resp = await cli.post("/auth/login", json=credentials)
        assert resp.status == 400
    
    # Unallowed attributes
    credentials = {"login": user["login"], "password": user["password"]}
    credentials["unallowed"] = "unallowed"
    resp = await cli.post("/auth/login", json=credentials)
    assert resp.status == 400

    # Incorrect values for general attributes
    for attr in ("login", "password"):
        for value in incorrect_user_attributes[attr]:
            if attr == "password" and type(value) == str: continue # min and max password lengths are tested separately
            credentials = {"login": user["login"], "password": user["password"]}
            credentials[attr] = value
            resp = await cli.post("/auth/login", json=credentials)
            assert resp.status == 400
            
    
    # Password with exceeing length (should be debounced manually)
    for value in ("", "a" * 73):
        credentials = {"login": user["login"], "password": value}
        resp = await cli.post("/auth/login", json=credentials)
        assert resp.status == 401 if len(value) == 73 else 400


async def test_incorrect_credentials(cli, db_cursor):
    # Insert a user
    user = get_test_user(2, pop_keys=["password_repeat"])
    insert_users([user], db_cursor)

    credentials = {"login": user["login"], "password": "incorrect password"}
    resp = await cli.post("/auth/login", json=credentials)
    assert resp.status == 401

    credentials = {"login": "incorrect login", "password": user["password"]}
    resp = await cli.post("/auth/login", json=credentials)
    assert resp.status == 401


async def test_failed_login_attempts_limiting(cli, db_cursor):
    # Insert a user
    user = get_test_user(2, pop_keys=["password_repeat"])
    insert_users([user], db_cursor)

    # Expected login timeouts in seconds
    _LOGIN_TIMEOUTS = [-60] * 9
    _LOGIN_TIMEOUTS.extend([5, 10, 20, 30, 60, 120, 600, 1200, 1800])
    _LOGIN_TIMEOUTS.extend([3600]*2) # additional values for checking `cant_login_until` updated value

    credentials = {"login": user["login"], "password": "wrong password"}
    ip_address = "127.0.0.1"

    for i in range(20):
        # Get current `failed_login_attempts` and `cant_login_until`
        db_cursor.execute(f"SELECT failed_login_attempts, cant_login_until FROM login_rate_limits WHERE ip_address = '{ip_address}'")
        lrl = db_cursor.fetchone() or (0, None)

        # Login with incorrect credentials
        resp = await cli.post("/auth/login", json=credentials)
        assert resp.status == 401 if i < 10 else 429

        # If `cant_login_until` > 0
        if i >= 10:
            # Access token was not issued
            db_cursor.execute("SELECT access_token FROM sessions WHERE user_id = 2")
            assert not db_cursor.fetchone()

            # Response contains correct `Retry-After` header
            assert resp.headers.get("Retry-After") == str(_LOGIN_TIMEOUTS[i - 1])

            # Check if login_rate_limits table was not updated
            db_cursor.execute(f"SELECT failed_login_attempts, cant_login_until FROM login_rate_limits WHERE ip_address = '{ip_address}'")
            rows = db_cursor.fetchall()
            assert len(rows) == 1
            assert rows[0] == lrl

            # Reset `cant_login_until`
            cant_login_until = datetime.now(tz=timezone.utc) + timedelta(seconds=-60)
            db_cursor.execute(f"UPDATE login_rate_limits SET cant_login_until = '{cant_login_until}' WHERE ip_address = '{ip_address}'")

            # Login with incorrect credentials
            resp = await cli.post("/auth/login", json=credentials)
        
        # Check response status
        assert resp.status == 401

        # Access token was not issued
        db_cursor.execute("SELECT access_token FROM sessions WHERE user_id = 2")
        assert not db_cursor.fetchone()

        # `failed_login_attempts` and `cant_login_until` are updated
        db_cursor.execute(f"SELECT failed_login_attempts, cant_login_until FROM login_rate_limits WHERE ip_address = '{ip_address}'")
        rows = db_cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == lrl[0] + 1 # `failed_login_attempts`
        # `cant_login_until` ~= datetime.now(tz=timezone.utc) + timeout after i+1 failed logins
        assert timedelta(seconds=0) <= datetime.now(tz=timezone.utc) - \
            (rows[0][1] - timedelta(seconds=_LOGIN_TIMEOUTS[i])) <= timedelta(seconds=1)


async def test_failed_login_attempts_limiting_forwarded_remote(cli, db_cursor):
    credentials = {"login": "wrong login", "password": "wrong password"}
    ip_address = "1.1.1.1"
    headers = {"Forwarded": f"for={ip_address}"}

    db_cursor.execute(f"SELECT failed_login_attempts FROM login_rate_limits WHERE ip_address = '{ip_address}'")
    assert not db_cursor.fetchone()

    # Login with incorrect credentials
    resp = await cli.post("/auth/login", json=credentials, headers=headers)
    assert resp.status == 401

    # Check if request.remote (which gives value for failed_login_attempts.ip_address) was correctly replaced by aiohttp-remotes middleware
    db_cursor.execute(f"SELECT failed_login_attempts FROM login_rate_limits WHERE ip_address = '{ip_address}'")
    assert db_cursor.fetchone() == (1,)


async def test_login_with_a_user_who_cant_login(cli, db_cursor):
    # Insert a user
    user = get_test_user(2, can_login=False, pop_keys=["password_repeat"])
    insert_users([user], db_cursor)
    
    # Login as a user with `can_login` = False
    credentials = {"login": user["login"], "password": user["password"]}
    resp = await cli.post("/auth/login", json=credentials)
    assert resp.status == 403


async def test_logging_in_with_correct_admin_credentials(cli, db_cursor, config):
    # Insert a user
    user = get_test_user(2, user_level="admin", pop_keys=["password_repeat"])
    insert_users([user], db_cursor)

    # Add a login rate limiting record
    ip_address = "127.0.0.1"
    cant_login_until = datetime.now(tz=timezone.utc) + timedelta(seconds=-60)
    db_cursor.execute(f"""INSERT INTO login_rate_limits (ip_address, failed_login_attempts, cant_login_until) VALUES 
                          ('{ip_address}', 5, '{cant_login_until}')""")
    db_cursor.execute(f"SELECT COUNT(*) FROM login_rate_limits WHERE ip_address = '{ip_address}'")
    assert db_cursor.fetchone() == (1,)

    credentials = {"login": user["login"], "password": user["password"]}
    resp = await cli.post("/auth/login", json=credentials)
    assert resp.status == 200

    # Check response
    data = await resp.json()
    assert "auth" in data
    assert "access_token" in data["auth"]
    expiration_time = datetime.fromisoformat(data["auth"]["access_token_expiration_time"])
    assert datetime.now(tz=timezone.utc) + timedelta(seconds=config["app"]["token_lifetime"]) \
        - expiration_time < timedelta(seconds=1)
    assert data["auth"]["user_id"] == user["user_id"]
    assert data["auth"]["user_level"] == user["user_level"]

    # Check if a session was created for the user in the database
    db_cursor.execute(f"""SELECT user_id, expiration_time FROM sessions WHERE access_token = '{data["auth"]["access_token"]}'""")
    row = db_cursor.fetchone()
    assert row[0] == 2
    assert expiration_time == row[1]

    # Check if login rate limiting record was removed from the database
    db_cursor.execute(f"SELECT COUNT(*) FROM login_rate_limits WHERE ip_address = '{ip_address}'")
    assert db_cursor.fetchone() == (0,)


async def test_register_and_login_with_registered_credentials(cli, db_cursor):    
    # Register a user
    user = get_test_user(2, user_level="admin", pop_keys=["user_id", "registered_at"])
    resp = await cli.post("/auth/register", json=user, headers=headers_admin_token)
    assert resp.status == 200

    # Login as registered user
    credentials = {"login": user["login"], "password": user["password"]}
    resp = await cli.post("/auth/login", json=credentials)
    assert resp.status == 200

    # Check if a session was created
    data = await resp.json()
    db_cursor.execute(f"""SELECT user_id FROM sessions WHERE access_token = '{data["auth"]["access_token"]}'""")
    assert db_cursor.fetchone() == (2, )


if __name__ == "__main__":
    run_pytest_tests(__file__)
