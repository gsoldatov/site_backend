"""
Tests for `object_id` attribute in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs
from tests.data_generators.sessions import headers_admin_token
from tests.db_operations.objects import insert_objects
from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_values(cli, db_cursor):
    # Missing attribute
    body = get_bulk_upsert_request_body()
    body["objects"][0].pop("object_id")
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    for value in [None, False, "a", {}, [], [1]]:
        body = get_bulk_upsert_request_body()
        body["objects"][0]["object_id"] = value
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_try_updating_a_non_existing_object(cli, db_cursor):
    # Insert an object into the database
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)

    # Try upserting a new object & 2 objects with existing IDs (one of which does not actully exist)
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0),
        get_bulk_upsert_object(object_id=1),
        get_bulk_upsert_object(object_id=999)
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_duplicate_object_ids(cli, db_cursor):
    # Insert an object into the database
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)

    # Duplicate new IDs
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object() for _ in range(2)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Duplicate existing IDs
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object(object_id=1) for _ in range(2)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_a_new_object(cli, db_cursor):
    # Insert an object
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)

    # Add a new object
    body = get_bulk_upsert_request_body()
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert len(data["objects_attributes_and_tags"]) == 1
    assert data["objects_attributes_and_tags"][0]["object_id"] == 2

    # Check database
    db_cursor.execute("SELECT object_id FROM objects WHERE object_id = 2")
    assert [r[0] for r in db_cursor.fetchall()] == [2]


async def test_update_an_existing_object(cli, db_cursor):
    # Insert an object
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)

    # Update an existing object
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1, object_name="updated name")
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert len(data["objects_attributes_and_tags"]) == 1
    assert data["objects_attributes_and_tags"][0]["object_id"] == 1
    # Check database
    db_cursor.execute("SELECT object_id, object_name FROM objects WHERE object_id = 1")
    rows = [r for r in db_cursor.fetchall()]
    assert [r[0] for r in rows] == [1]
    assert rows[0][1] == "updated name"


async def test_upsert_multiple_objects(cli, db_cursor):
    # Insert 2 objects
    insert_objects([
        get_object_attrs(1) for i in range(2)]
    , db_cursor, generate_ids=True)

    # Upsert objects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0),
        get_bulk_upsert_object(object_id=-1),
        get_bulk_upsert_object(object_id=1, object_name="updated name 1"),
        get_bulk_upsert_object(object_id=2, object_name="updated name 2")
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    received_object_ids_attributes = [o["object_id"] for o in data["objects_attributes_and_tags"]]
    assert sorted(received_object_ids_attributes) == [1, 2, 3, 4]

    # Check database
    db_cursor.execute("SELECT object_id, object_name FROM objects WHERE object_id IN (1, 2, 3, 4)")
    rows = sorted([r for r in db_cursor.fetchall()], key=lambda r: r[0])
    assert [r[0] for r in rows] == [1, 2, 3, 4]
    assert [rows[0][1], rows[1][1]] == ["updated name 1", "updated name 2"]


if __name__ == "__main__":
    run_pytest_tests(__file__)
