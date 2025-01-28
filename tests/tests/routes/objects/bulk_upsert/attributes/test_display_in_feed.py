"""
Tests for `display_in_feed` attribute in /objects/upsert route.
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
    body["objects"][0].pop("display_in_feed")
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    for value in [None, 1, "a", {}, [], [1]]:
        body = get_bulk_upsert_request_body()
        body["objects"][0]["display_in_feed"] = value
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_add_new_objects(cli, db_cursor):
    # Add new objects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, display_in_feed=True),
        get_bulk_upsert_object(object_id=-1, display_in_feed=False)
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    received_values = [
        o["display_in_feed"] for o in sorted(data["objects_attributes_and_tags"], key=lambda x: x["object_id"])
    ]
    assert received_values == [True, False]

    # Check database
    db_cursor.execute("SELECT display_in_feed FROM objects WHERE object_id IN (1, 2) ORDER BY object_id")
    assert [r[0] for r in db_cursor.fetchall()] == [True, False]


async def test_update_an_object(cli, db_cursor):
    # Insert an object into the database
    insert_objects([get_test_object(1, display_in_feed=False, owner_id=1, pop_keys=["object_data"])], db_cursor, generate_ids=True)

    # Update an object
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object(object_id=1, display_in_feed=True)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["display_in_feed"] == True

    # Check database
    db_cursor.execute("SELECT display_in_feed FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == True


if __name__ == "__main__":
    run_pytest_tests(__file__)
