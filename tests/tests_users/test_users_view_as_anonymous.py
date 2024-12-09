from datetime import datetime

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.users import get_test_user, insert_users


async def test_valid_request_for_basic_view(cli, db_cursor):
    # Insert users
    users = [get_test_user(i, pop_keys=["password_repeat"]) for i in range(2, 6)]
    insert_users(users, db_cursor) 

    # Send request and check response
    body = {"user_ids": [i for i in range(1, 11)]}
    body["full_view_mode"] = False  # Check if non-admin can use false `full_view_mode`
    resp = await cli.post("/users/view", json=body)
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


async def test_valid_request_for_full_view(cli):
    body = {"user_ids": [i for i in range(1, 11)], "full_view_mode": True}
    resp = await cli.post("/users/view", json=body)
    assert resp.status == 401


if __name__ == "__main__":
    run_pytest_tests(__file__)
