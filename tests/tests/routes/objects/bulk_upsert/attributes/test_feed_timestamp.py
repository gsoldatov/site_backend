"""
Tests for `feed_timestamp` attribute in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from datetime import datetime, timezone, timedelta

from tests.data_generators.objects import get_object_attrs
from tests.data_generators.sessions import headers_admin_token
from tests.db_operations.objects import insert_objects
from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_values(cli, db_cursor):
    # Missing attribute
    body = get_bulk_upsert_request_body()
    body["objects"][0].pop("feed_timestamp")
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    for value in [1, True, "a", {}, [], [1]]:
        body = get_bulk_upsert_request_body()
        body["objects"][0]["feed_timestamp"] = value
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_add_new_objects(cli, db_cursor):
    # Add new objects
    feed_timestamp = datetime.now(tz=timezone.utc) - timedelta(days=1)
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, feed_timestamp=None),
        get_bulk_upsert_object(object_id=-1, feed_timestamp=feed_timestamp)
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    received_values = [
        datetime.fromisoformat(o["feed_timestamp"]) if o["feed_timestamp"] is not None else o["feed_timestamp"]
        for o in sorted(data["objects_attributes_and_tags"], key=lambda x: x["object_id"])
    ]
    assert received_values == [None, feed_timestamp]

    # Check database
    db_cursor.execute("SELECT feed_timestamp FROM objects WHERE object_id IN (1, 2) ORDER BY object_id")
    assert [r[0] for r in db_cursor.fetchall()] == [None, feed_timestamp]


async def test_update_an_object(cli, db_cursor):
    # Insert an object into the database
    feed_timestamp = datetime.now(tz=timezone.utc) - timedelta(days=1)
    insert_objects([get_object_attrs(1, feed_timestamp=feed_timestamp)], db_cursor, generate_ids=True)

    # Update an object
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object(object_id=1, feed_timestamp=None)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["feed_timestamp"] == None

    # Check database
    db_cursor.execute("SELECT feed_timestamp FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == None


if __name__ == "__main__":
    run_pytest_tests(__file__)
