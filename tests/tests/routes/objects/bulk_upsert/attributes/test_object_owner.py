"""
Tests for `owner_id` attribute in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.users import get_test_user

from tests.db_operations.objects import insert_objects
from tests.db_operations.users import insert_users

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_values(cli, db_cursor):
    # Missing attribute
    body = get_bulk_upsert_request_body()
    body["objects"][0].pop("owner_id")
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    for value in [True, "a", {}, [], [1], -1, 0]:
        body = get_bulk_upsert_request_body()
        body["objects"][0]["owner_id"] = value
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_set_a_non_existing_owner_id(cli, db_cursor):
    # Missing attribute
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(owner_id=999)
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_a_new_object(cli, db_cursor):
    # Add a new object
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object(owner_id=1)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["owner_id"] == 1

    # Check database
    db_cursor.execute("SELECT owner_id FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == 1


async def test_update_an_object(cli, db_cursor):
    # Insert an object and another user into the database
    insert_objects([get_test_object(1, owner_id=1, pop_keys=["object_data"])], db_cursor, generate_ids=True)
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor)

    # Update an object (set another user)
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object(object_id=1, owner_id=2)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["owner_id"] == 2

    # Check database
    db_cursor.execute("SELECT owner_id FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == 2


if __name__ == "__main__":
    run_pytest_tests(__file__)
