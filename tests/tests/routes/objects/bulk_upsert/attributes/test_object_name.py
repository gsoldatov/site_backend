"""
Tests for `object_name` attribute in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token
from tests.db_operations.objects import insert_objects
from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_values(cli, db_cursor):
    # Missing attribute
    body = get_bulk_upsert_request_body()
    body["objects"][0].pop("object_name")
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    for value in [None, False, 1, {}, [], [1], "", "a" * 256]:
        body = get_bulk_upsert_request_body()
        body["objects"][0]["object_name"] = value
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_add_a_new_object(cli, db_cursor):
    # Add a new object
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object()])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["object_name"] == body["objects"][0]["object_name"]

    # Check database
    db_cursor.execute("SELECT object_name FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == body["objects"][0]["object_name"]


async def test_update_an_object(cli, db_cursor):
    # Insert an object into the database
    object_name = "updated object name"
    insert_objects([get_test_object(1, owner_id=1, pop_keys=["object_data"])], db_cursor, generate_ids=True)

    # Update an object
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object(object_id=1, object_name=object_name)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["object_name"] == object_name

    # Check database
    db_cursor.execute("SELECT object_name FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == object_name


if __name__ == "__main__":
    run_pytest_tests(__file__)
