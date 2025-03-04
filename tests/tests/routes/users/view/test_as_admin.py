from datetime import datetime

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.users import get_test_user

from tests.db_operations.users import insert_users


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.post("/users/view", data="not a JSON document.")
    assert resp.status == 400

    # Required attributes missing
    for attr in ("user_ids",):
        body = {"full_view_mode": False, "user_ids": [1]}
        body.pop(attr)
        resp = await cli.post("/users/view", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect & unallowed attributes
    incorrect_attributes = {
        "user_ids": [None, False, 1, "str", {}, [], ["a"], [0], [1] * 1001],
        "full_view_mode": [None, 1, "str", {}, []],
        "unallowed": ["unallowed"]
    }
    for attr, values in incorrect_attributes.items():
        for value in values:
            body = {"full_view_mode": False, "user_ids": [1]}
            body[attr] = value
            resp = await cli.post("/users/view", json=body, headers=headers_admin_token)
            assert resp.status == 400
    

async def test_valid_request_for_non_existing_users(cli):
    body = {"user_ids": [1001, 1002]}
    resp = await cli.post("/users/view", json=body, headers=headers_admin_token)
    assert resp.status == 404


async def test_valid_request_for_basic_view(cli, db_cursor):
    # Insert users
    users = [get_test_user(i, pop_keys=["password_repeat"]) for i in range(2, 6)]
    insert_users(users, db_cursor) 

    # Send request and check response
    body = {"user_ids": [i for i in range(1, 11)]}
    resp = await cli.post("/users/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    
    data = await resp.json()
    assert type(data.get("users")) == list
    assert len(data["users"]) == 5
    assert sorted([u["user_id"] for u in data["users"]]) == [1, 2, 3, 4, 5]

    # Check user data
    for user in data["users"]:
        assert type(user) == dict
        assert sorted(list(user.keys())) == ["registered_at", "user_id", "username"]

        if user["user_id"] == 2:
            response_registered_at = datetime.fromisoformat(user["registered_at"])
            assert response_registered_at == users[0]["registered_at"]
            assert user["username"] == users[0]["username"]


async def test_valid_request_for_full_view(cli, db_cursor):
    # Insert users
    users = [get_test_user(i, pop_keys=["password_repeat"]) for i in range(2, 6)]
    users[0]["user_level"] = "admin"
    insert_users(users, db_cursor) 

    # Send request and check response
    body = {"user_ids": [i for i in range(1, 11)], "full_view_mode": True}
    resp = await cli.post("/users/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    
    data = await resp.json()
    assert type(data.get("users")) == list
    assert len(data["users"]) == 5
    assert sorted([u["user_id"] for u in data["users"]]) == [1, 2, 3, 4, 5]
    
    # Check user data
    for user in data["users"]:
        assert type(user) == dict
        attrs = ("user_id", "registered_at", "username", "user_level", "can_login", "can_edit_objects")
        for attr in attrs: assert attr in user
        assert len(user.keys()) == len(attrs)

        if user["user_id"] == 2:
            response_registered_at = datetime.fromisoformat(user["registered_at"])
            assert response_registered_at == users[0]["registered_at"]
            for attr in attrs:
                if attr != "registered_at":
                    assert user[attr] == users[0][attr]


if __name__ == "__main__":
    run_pytest_tests(__file__)
