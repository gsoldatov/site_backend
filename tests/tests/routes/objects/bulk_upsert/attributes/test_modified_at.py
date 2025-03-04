"""
Tests for `modified_at` attribute in /objects/upsert route.
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


async def test_add_a_new_object(cli, db_cursor):
    # Add a new object
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object()])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    now = datetime.now(tz=timezone.utc)
    received_modified_at = datetime.fromisoformat(data["objects_attributes_and_tags"][0]["modified_at"])
    assert now - timedelta(seconds=1) <= received_modified_at <= now + timedelta(seconds=1)

    # Check database
    db_cursor.execute("SELECT modified_at FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == received_modified_at


async def test_update_an_object(cli, db_cursor):
    # Insert an object into the database
    old_modified_at = datetime.now(tz=timezone.utc) - timedelta(days=1)
    insert_objects([get_object_attrs(1, modified_at=old_modified_at)], db_cursor, generate_ids=True)

    # Update an object
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object(object_id=1)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    now = datetime.now(tz=timezone.utc)
    received_modified_at = datetime.fromisoformat(data["objects_attributes_and_tags"][0]["modified_at"])
    assert now - timedelta(seconds=1) <= received_modified_at <= now + timedelta(seconds=1)

    # Check database
    db_cursor.execute("SELECT modified_at FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == received_modified_at


if __name__ == "__main__":
    run_pytest_tests(__file__)
