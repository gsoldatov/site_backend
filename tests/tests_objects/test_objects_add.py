import pytest
from datetime import datetime

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.objects import get_test_object, incorrect_object_values
from tests.fixtures.data_generators.sessions import headers_admin_token

from tests.fixtures.data_generators.users import get_test_user
from tests.fixtures.db_operations.users import insert_users


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.post("/objects/add", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Required attributes missing
    for attr in ("object_type", "object_name", "object_description", "is_published", "display_in_feed", "feed_timestamp", "show_description"):
        link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
        link.pop(attr)
        resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
        assert resp.status == 400

    # Unallowed attributes
    link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    link["unallowed"] = "unallowed"
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values for general attributes
    for k, v in incorrect_object_values:
        if k != "object_id":
            link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
            link[k] = v
            resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
            assert resp.status == 400


async def test_add_object_with_incorrect_data(cli):
    # Non-existing owner_id
    link = get_test_object(1, owner_id=1000, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_two_objects_with_the_same_name(cli, db_cursor):
    # Add a correct object
    link = get_test_object(1, is_published=True, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert "object" in resp_json
    resp_object = resp_json["object"]
    assert type(resp_object) == dict
    for attr in ("object_id", "object_type", "created_at", "modified_at", "object_name", "object_description"):
        assert attr in resp_object
    for attr in ("object_name", "object_description", "is_published", "display_in_feed", "feed_timestamp", "show_description"):
        if attr == "feed_timestamp":
            assert datetime.fromisoformat(link[attr][:-1]) == datetime.fromisoformat(resp_object[attr])
        else:
            assert link[attr] == resp_object[attr]

    db_cursor.execute(f"SELECT object_name FROM objects WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (link["object_name"],)

    # Check if an object with existing name is added
    # Also check empty feed timestamp case
    link = get_test_object(1, feed_timestamp="", pop_keys=["object_id", "created_at", "modified_at"])
    link["object_name"] = link["object_name"].upper()
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    assert (await resp.json())["object"]["feed_timestamp"] == ""


@pytest.mark.parametrize("owner_id", [1, 2])    # set the same and another owner_id
async def test_add_object_with_set_owner_id(cli, db_cursor, owner_id):
    # Add a second user
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor)

    # Add a correct object with set owner_id
    link = get_test_object(1, owner_id=owner_id, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    resp_object = (await resp.json())["object"]
    assert link["owner_id"] == resp_object["owner_id"]

    db_cursor.execute(f"SELECT owner_id FROM objects WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (owner_id,)


if __name__ == "__main__":
    run_pytest_tests(__file__)
