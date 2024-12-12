from datetime import datetime, timezone, timedelta

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.users import get_test_user

from tests.fixtures.data_sets.users import incorrect_user_attributes

from tests.fixtures.db_operations.settings import set_setting
from tests.fixtures.db_operations.users import insert_users


async def test_incorrect_request_body(cli, db_cursor):
    # Enable non-admin user registration
    set_setting(db_cursor, "non_admin_registration_allowed", "TRUE")

    # Incorrect request body
    resp = await cli.post("/auth/register", data="not a JSON document.")
    assert resp.status == 400

    # Required attributes missing
    for attr in ("login", "password", "password_repeat", "username"):
        user = get_test_user(2, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
        user.pop(attr)
        resp = await cli.post("/auth/register", json=user)
        assert resp.status == 400
    
    # Unallowed attributes
    user = get_test_user(2, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    user["unallowed"] = "unallowed"
    resp = await cli.post("/auth/register", json=user)
    assert resp.status == 400

    # Incorrect values for general attributes
    for attr in ("login", "password", "password_repeat", "username"):
        for value in incorrect_user_attributes[attr]:
            user = get_test_user(2, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
            user[attr] = value
            resp = await cli.post("/auth/register", json=user)
            assert resp.status == 400


async def test_password_not_matching_repeat(cli, db_cursor):
    # Enable non-admin user registration
    set_setting(db_cursor, "non_admin_registration_allowed", "TRUE")

    user = get_test_user(2, password="a"*10, password_repeat="b"*10, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    resp = await cli.post("/auth/register", json=user)
    assert resp.status == 400


async def test_existing_login_and_username(cli, db_cursor):
    # Enable non-admin user registration
    set_setting(db_cursor, "non_admin_registration_allowed", "TRUE")

    # Add an existing user
    existing_login, existings_username = "existing login", "existing_username"
    insert_users([get_test_user(10, login=existing_login, username=existings_username, pop_keys=["password_repeat"])], db_cursor)

    user = get_test_user(2, login=existing_login, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    resp = await cli.post("/auth/register", json=user)
    assert resp.status == 400

    user = get_test_user(2, username=existings_username, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    resp = await cli.post("/auth/register", json=user)
    assert resp.status == 400


async def test_passing_privilege(cli, db_cursor):
    # Enable non-admin user registration
    set_setting(db_cursor, "non_admin_registration_allowed", "TRUE")

    for attr, value in [("user_level", "admin"), ("can_login", True), ("can_edit_objects", True)]:
        user = get_test_user(2, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
        user[attr] = value
        resp = await cli.post("/auth/register", json=user)
        assert resp.status == 403


async def test_correct_request_with_registation_not_allowed(cli):
    user = get_test_user(2, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    resp = await cli.post("/auth/register", json=user)
    assert resp.status == 403


async def test_correct_request_with_omitted_privileges(cli, db_cursor):
    # Enable non-admin user registration
    set_setting(db_cursor, "non_admin_registration_allowed", "TRUE")
    
    current_time = datetime.now(tz=timezone.utc)
    user = get_test_user(2, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    resp = await cli.post("/auth/register", json=user)
    assert resp.status == 200

    # Check response
    assert await resp.text() == ""
    
    # Check database
    db_cursor.execute("SELECT registered_at, login, username, user_level, can_login, can_edit_objects FROM users WHERE user_id = 2")
    row = db_cursor.fetchone()
    assert row is not None
    assert timedelta(seconds=0) <= row[0] - current_time <= timedelta(seconds=1)
    assert row[1] == user["login"]
    assert row[2] == user["username"]
    assert row[3] == "user"
    assert row[4] == True
    assert row[5] == True


if __name__ == "__main__":
    run_pytest_tests(__file__)
