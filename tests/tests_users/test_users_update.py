from copy import deepcopy

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.sessions import headers_admin_token

from tests.fixtures.data_generators.users import get_test_user, get_update_user_request_body
from tests.fixtures.data_sets.users import incorrect_user_attributes
from tests.fixtures.db_operations.users import insert_users


async def test_incorrect_request_body_at_top_level(cli, config):
    # Incorrect request body
    resp = await cli.put("/users/update", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Required attributes missing
    for attr in ("user", "token_owner_password"):
        body = get_update_user_request_body(token_owner_password=config["app"]["default_user"]["password"].value)
        body.pop(attr)
        resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed attributes
    body = get_update_user_request_body(token_owner_password=config["app"]["default_user"]["password"].value)
    body["unallowed"] = "unallowed"
    resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # # Incorrect values for general attributes
    for (key, value) in [("user", False), ("user", 123), ("user", "str"), ("token_owner_password", False), ("token_owner_password", 123), 
        ("token_owner_password", "a"*7), ("token_owner_password", "a"*73)]:
        body = get_update_user_request_body(token_owner_password=config["app"]["default_user"]["password"].value)
        body[key] = value
        resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_incorrect_request_body_at_user_level(cli, config):
    # Missing user_id
    body = get_update_user_request_body(token_owner_password=config["app"]["default_user"]["password"].value)
    body["user"].pop("user_id")
    resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # No updated attributes are passed
    body = get_update_user_request_body(user={"user_id": 1}, token_owner_password=config["app"]["default_user"]["password"].value)
    resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Password is passed without repeat
    body = get_update_user_request_body(token_owner_password=config["app"]["default_user"]["password"].value)
    body["user"].pop("password_repeat")
    resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Unallowed attribute
    body = get_update_user_request_body(token_owner_password=config["app"]["default_user"]["password"].value)
    body["user"]["unallowed"] = "unallowed"
    resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect attribute values
    incorrect_attributes = deepcopy(incorrect_user_attributes)
    incorrect_attributes["user_id"] = [0, "str", True]

    for attr in incorrect_attributes:
        for value in incorrect_attributes[attr]:
            body = get_update_user_request_body(token_owner_password=config["app"]["default_user"]["password"].value)
            body["user"][attr] = value
            if attr == "password": body["user"]["password_repeat"] = value
            resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
            assert resp.status == 400
            

async def test_incorrect_body_attribute_values(cli, config):
    # Password is not correctly repeated
    body = get_update_user_request_body(token_owner_password=config["app"]["default_user"]["password"].value)
    body["user"]["password_repeat"] = "another password value"
    resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Token owner password is incorrect
    body = get_update_user_request_body(token_owner_password="incorrect password")
    resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Updated user does not exist
    body = get_update_user_request_body(token_owner_password=config["app"]["default_user"]["password"].value)
    body["user"]["user_id"] = 1000
    resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
    assert resp.status == 404


async def test_correct_update_of_a_single_attribute_of_another_user(cli, config, db_cursor):
    # Declare mock data & insert user
    user_id = 2
    initial_user_data = get_test_user(user_id, pop_keys=["password_repeat"])
    insert_users([initial_user_data], db_cursor)
    updated_user_data = [("login", "new login"), ("username", "new username"), ("password", "new password"), ("user_level", "user"), 
        ("can_login", False), ("can_edit_objects", False)]
    
    # Update each attribute separately
    for i, (attr, value) in enumerate(updated_user_data):
        user = {"user_id": user_id, attr: value}
        if attr == "password": user["password_repeat"] = value

        body = get_update_user_request_body(user, token_owner_password=config["app"]["default_user"]["password"].value)
        resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
        assert resp.status == 200

        # Check user attributes in the database
        db_cursor.execute(f"SELECT login, username, user_level, can_login, can_edit_objects FROM users WHERE user_id = {user_id}")
        row = db_cursor.fetchone()
        assert row[0] == updated_user_data[0][1]
        assert row[1] == updated_user_data[1][1] if i > 0 else initial_user_data["username"]
        assert row[2] == updated_user_data[3][1] if i > 2 else initial_user_data["user_level"]
        assert row[3] == updated_user_data[4][1] if i > 3 else initial_user_data["can_login"]
        assert row[4] == updated_user_data[5][1] if i > 4 else initial_user_data["can_edit_objects"]

        # Try to login as a user with a new password
        if i == 2:
            resp = await cli.post("/auth/login", json={"login": updated_user_data[0][1], "password": updated_user_data[2][1]})
            resp = await cli.post("/auth/login", json={"login": updated_user_data[0][1], "password": updated_user_data[2][1]})
            db_cursor.execute(f"SELECT COUNT(*) FROM sessions WHERE user_id = {user_id}")
            assert db_cursor.fetchone()[0] == 2

        # Check if user sessions were removed after `can_login` was set to false
        if i == 4:
            db_cursor.execute(f"SELECT COUNT(*) FROM sessions WHERE user_id = {user_id}")
            assert db_cursor.fetchone()[0] == 0

    
async def test_correct_update_of_multiple_attributes_of_the_same_user(cli, config, db_cursor):
    updated_user_data = get_test_user(1, login="updated login", username="updated username", password="updated_password", user_level="user",
        can_login=False, can_edit_objects=False, pop_keys=["registered_at"])
    
    body = get_update_user_request_body(user=updated_user_data, token_owner_password=config["app"]["default_user"]["password"].value)
    resp = await cli.put("/users/update", json=body, headers=headers_admin_token)
    assert resp.status == 200

    # Check user attributes in the database
    db_cursor.execute(f"SELECT login, username, user_level, can_login, can_edit_objects FROM users WHERE user_id = 1")
    row = db_cursor.fetchone()
    assert row[0] == updated_user_data["login"]
    assert row[1] == updated_user_data["username"]
    assert row[2] == updated_user_data["user_level"]
    assert row[3] == updated_user_data["can_login"]
    assert row[4] == updated_user_data["can_edit_objects"]

    # Allow user to login
    db_cursor.execute("UPDATE users SET can_login = true WHERE user_id = 1")

    # Try to login with new credentials
    resp = await cli.post("/auth/login", json={"login": updated_user_data["login"], "password": updated_user_data["password"]})
    db_cursor.execute(f"SELECT COUNT(*) FROM sessions WHERE user_id = 1")
    assert db_cursor.fetchone()[0] == 1


if __name__ == "__main__":
    run_pytest_tests(__file__)
