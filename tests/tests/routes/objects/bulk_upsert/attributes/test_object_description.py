"""
Tests for `object_name` attribute in /objects/upsert route.
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
    body["objects"][0].pop("object_description")
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    for value in [None, False, 1, {}, [], [1]]:
        body = get_bulk_upsert_request_body()
        body["objects"][0]["object_description"] = value
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_add_new_objects(cli, db_cursor):
    # Add new objects
    expected_descriptions = ["", "new description"]
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_description=expected_descriptions[0]),
        get_bulk_upsert_object(object_id=-1, object_description=expected_descriptions[1])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    received_descriptions = [
        o["object_description"] for o in sorted(data["objects_attributes_and_tags"], key=lambda x: x["object_id"])
    ]
    assert received_descriptions == expected_descriptions

    # Check database
    db_cursor.execute("SELECT object_description FROM objects WHERE object_id IN (1, 2) ORDER BY object_id")
    assert [r[0] for r in db_cursor.fetchall()] == received_descriptions


async def test_update_an_object(cli, db_cursor):
    # Insert an object into the database
    object_description = "updated object description"
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)

    # Update an object
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object(object_id=1, object_description=object_description)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["object_description"] == object_description

    # Check database
    db_cursor.execute("SELECT object_description FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == object_description


if __name__ == "__main__":
    run_pytest_tests(__file__)
