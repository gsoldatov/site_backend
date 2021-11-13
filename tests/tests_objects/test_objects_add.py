import pytest

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.fixtures.objects import get_test_object, incorrect_object_values
from tests.fixtures.sessions import headers_admin_token
from tests.fixtures.users import get_test_user, insert_users


async def test_incorrect_request_body_as_admin(cli):
    # Incorrect request body
    resp = await cli.post("/objects/add", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Required attributes missing
    for attr in ("object_type", "object_name", "object_description", "is_published", "show_description"):
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


async def test_add_object_with_incorrect_data_as_admin(cli):
    # Non-existing owner_id
    link = get_test_object(1, owner_id=1000, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_two_objects_with_the_same_name_as_admin(cli, db_cursor):
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
    for attr in ("object_name", "object_description", "is_published", "show_description"):
        assert link[attr] == resp_object[attr]

    db_cursor.execute(f"SELECT object_name FROM objects WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (link["object_name"],)

    # Check if an object with existing name is added
    link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    link["object_name"] = link["object_name"].upper()
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200


@pytest.mark.parametrize("owner_id", [1, 2])    # set the same and another owner_id
async def test_add_object_with_set_owner_id_as_admin(cli, db_cursor, owner_id):
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


async def test_add_a_correct_object_as_anonymous(cli, db_cursor):
    link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": link})
    assert resp.status == 401

    db_cursor.execute(f"SELECT object_name FROM objects")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
