if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.sessions import headers_admin_token
from tests.fixtures.users import get_test_user, insert_users


async def test_valid_log_in(cli, db_cursor):
    # Insert a user
    user = get_test_user(2, pop_keys=["password_repeat"])
    insert_users([user], db_cursor)

    credentials = {"login": user["login"], "password": user["password"]}
    resp = await cli.post("/auth/login", json=credentials, headers=headers_admin_token)
    assert resp.status == 403


if __name__ == "__main__":
    run_pytest_tests(__file__)
