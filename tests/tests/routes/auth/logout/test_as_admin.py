if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.sessions import admin_token, non_existing_token, headers_admin_token, headers_non_existing_token


async def test_correct_logout(cli, db_cursor):
    # Check if token exists
    db_cursor.execute(f"SELECT user_id FROM sessions WHERE access_token = '{admin_token}'")
    rows = db_cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == 1

    # Logout
    resp = await cli.post("/auth/logout", headers=headers_admin_token)
    assert resp.status == 200

    # Check if token was removed
    db_cursor.execute(f"SELECT user_id FROM sessions WHERE access_token = '{admin_token}'")
    assert not db_cursor.fetchone()


async def test_logout_with_non_existing_token(cli, db_cursor):
    # Check if token does not exist
    db_cursor.execute(f"SELECT user_id FROM sessions WHERE access_token = '{non_existing_token}'")
    assert not db_cursor.fetchone()

    resp = await cli.post("/auth/logout", headers=headers_non_existing_token)
    assert resp.status == 200


if __name__ == "__main__":
    run_pytest_tests(__file__)
