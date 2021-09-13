from datetime import datetime, timedelta

import pytest

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.fixtures.settings import set_setting
from tests.fixtures.users import headers_admin_token, incorrect_user_attributes, get_test_user, insert_users


async def test_incorrect_request_body_as_anonymous(cli, db_cursor, config):
    # Enable non-admin user registration
    set_setting("non_admin_registration_allowed", "TRUE", db_cursor, config)

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


async def test_incorrect_request_body_as_admin(cli, db_cursor, config):
    # Incorrect request body
    resp = await cli.post("/auth/register", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Required attributes missing
    for attr in ("login", "password", "password_repeat", "username"):
        user = get_test_user(2, pop_keys=["user_id", "registered_at"])
        user.pop(attr)
        resp = await cli.post("/auth/register", json=user, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed attributes
    user = get_test_user(2, pop_keys=["user_id", "registered_at"])
    user["unallowed"] = "unallowed"
    resp = await cli.post("/auth/register", json=user, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values for general attributes
    for attr in ("login", "password", "password_repeat", "username", "user_level", "can_login", "can_edit_objects"):
        for value in incorrect_user_attributes[attr]:
            user = get_test_user(2, pop_keys=["user_id", "registered_at"])
            user[attr] = value
            resp = await cli.post("/auth/register", json=user, headers=headers_admin_token)
            assert resp.status == 400


@pytest.mark.parametrize("headers", [None, headers_admin_token])
async def test_password_not_matching_repeat_as_admin_and_anonymous(cli, db_cursor, config, headers):
    # Enable non-admin user registration
    set_setting("non_admin_registration_allowed", "TRUE", db_cursor, config)

    user = get_test_user(2, password="a"*10, password_repeat="b"*10, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    resp = await cli.post("/auth/register", json=user, headers=headers)
    assert resp.status == 400


@pytest.mark.parametrize("headers", [None, headers_admin_token])
async def test_existing_login_and_username_as_admin_and_anonymous(cli, db_cursor, config, headers):
    # Enable non-admin user registration
    if headers is None:
        set_setting("non_admin_registration_allowed", "TRUE", db_cursor, config)

    # Add an existing user
    existing_login, existings_username = "existing login", "existing_username"
    # insert_users([get_test_user(2, login=existing_login, username=existings_username, pop_keys=["password_repeat"])], db_cursor, config)
    insert_users([get_test_user(10, login=existing_login, username=existings_username, pop_keys=["password_repeat"])], db_cursor, config)

    user = get_test_user(2, login=existing_login, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    resp = await cli.post("/auth/register", json=user, headers=headers)
    assert resp.status == 400

    user = get_test_user(2, username=existings_username, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    resp = await cli.post("/auth/register", json=user, headers=headers)
    assert resp.status == 400


async def test_passing_privilege_as_anonymous(cli, db_cursor, config):
    # Enable non-admin user registration
    set_setting("non_admin_registration_allowed", "TRUE", db_cursor, config)

    for attr, value in [("user_level", "admin"), ("can_login", True), ("can_edit_objects", True)]:
        user = get_test_user(2, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
        user[attr] = value
        resp = await cli.post("/auth/register", json=user)
        assert resp.status == 403


async def test_correct_request_with_registation_not_allowed_as_anonymous(cli, db_cursor, config):
    user = get_test_user(2, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    resp = await cli.post("/auth/register", json=user)
    assert resp.status == 403


@pytest.mark.parametrize("headers", [None, headers_admin_token])
async def test_correct_request_with_omitted_privileges_as_admin_and_anonymous(cli, db_cursor, config, headers):
    # Enable non-admin user registration
    if headers is None:
        set_setting("non_admin_registration_allowed", "TRUE", db_cursor, config)
    
    current_time = datetime.utcnow()
    user = get_test_user(2, pop_keys=["user_id", "registered_at", "user_level", "can_login", "can_edit_objects"])
    resp = await cli.post("/auth/register", json=user, headers=headers)
    assert resp.status == 200

    # Check response
    data = await resp.json()
    assert type(data.get("user")) == dict
    assert data["user"]["user_id"] == 2    # admin is inserted with user_id = 1 by fixtures
    assert data["user"]["login"] == user["login"]
    assert "password" not in data["user"]
    assert data["user"]["username"] == user["username"]

    privilege_data_is_expected = headers is not None
    for attr in ("user_level", "can_login", "can_edit_objects"):
        assert (attr in data["user"]) == privilege_data_is_expected
    
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


async def test_correct_request_with_privileges_as_admin(cli, db_cursor, config):    
    current_time = datetime.utcnow()
    user = get_test_user(2, user_level="admin", can_login=False, can_edit_objects=False, pop_keys=["user_id", "registered_at"])
    resp = await cli.post("/auth/register", json=user, headers=headers_admin_token)
    assert resp.status == 200

    # Check response (privilege fields, others are checks in previous test)
    data = await resp.json()
    assert data["user"]["user_level"] == user["user_level"]
    assert data["user"]["can_login"] == user["can_login"]
    assert data["user"]["can_edit_objects"] == user["can_edit_objects"]

    # Check database
    db_cursor.execute("SELECT user_level, can_login, can_edit_objects FROM users WHERE user_id = 2")
    row = db_cursor.fetchone()
    assert row is not None
    assert row[0] == user["user_level"]
    assert row[1] == user["can_login"]
    assert row[2] == user["can_edit_objects"]


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
