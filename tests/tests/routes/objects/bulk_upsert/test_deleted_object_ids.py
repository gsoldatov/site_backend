"""
Tests for `deleted_object_ids` list in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs, get_test_object_data, get_composite_data, \
    get_composite_subobject_data
from tests.data_generators.sessions import headers_admin_token
from tests.db_operations.objects import insert_objects, insert_links, insert_composite
from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_values(cli, db_cursor):
    # Missing attribute
    body = get_bulk_upsert_request_body()
    body.pop("deleted_object_ids")
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    for value in [None, False, 1, "str", {}, [None], [False], [{}], ["a"], [-1], [0], [1] * 1001]:
        body = get_bulk_upsert_request_body()
        body["deleted_object_ids"] = value
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_upserted_objects_marked_as_fully_deleted(cli, db_cursor):
    body = get_bulk_upsert_request_body(
        objects=[get_bulk_upsert_object(object_id=1)],
        deleted_object_ids=[1]
    )
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_upserted_subobjects_marked_as_fully_deleted(cli, db_cursor):
    # Insert existing subobject
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(1)], db_cursor)

    body = get_bulk_upsert_request_body(
        objects=[get_bulk_upsert_object(object_type="composite", object_data=get_composite_data(
            subobjects=[get_composite_subobject_data(1, 0, 0)]
        ))],
        deleted_object_ids=[1]
    )
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_fully_delete_non_existing_object_id(cli, db_cursor):
    body = get_bulk_upsert_request_body(
        objects=[get_bulk_upsert_object()],
        deleted_object_ids=[999]
    )
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200


async def test_fully_delete_object_id_created_during_request(cli, db_cursor):
    body = get_bulk_upsert_request_body(
        objects=[get_bulk_upsert_object()],
        deleted_object_ids=[1]
    )
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200

    # Check if new object does not exist in the database
    db_cursor.execute("SELECT object_id FROM objects WHERE object_id = 1")
    assert not db_cursor.fetchone()


async def test_fully_delete_subobjects_of_other_objects(cli, db_cursor):
    # Insert an existing object & its subobject
    insert_objects([
        get_object_attrs(1),
        get_object_attrs(2, object_type="composite")
    ], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_composite([{
        "object_id": 2,
        "object_data": get_composite_data(subobjects=[get_composite_subobject_data(1, 0, 0)])
    }], db_cursor)

    body = get_bulk_upsert_request_body(
        objects=[get_bulk_upsert_object()],
        deleted_object_ids=[1]
    )
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200

    # Check if object was deleted
    db_cursor.execute("SELECT object_id FROM objects WHERE object_id = 1")
    assert not db_cursor.fetchone()


async def test_fully_deleted_removed_subobject_of_an_upserted_composite_object(cli, db_cursor):
    # Insert an existing object & its subobject
    insert_objects([
        get_object_attrs(1),
        get_object_attrs(2, object_type="composite")
    ], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_composite([{
        "object_id": 2,
        "object_data": get_composite_data(subobjects=[get_composite_subobject_data(1, 0, 0)])
    }], db_cursor)

    # Update existing composite object, remove its subobject & mark it as fully deleted
    body = get_bulk_upsert_request_body(
        objects=[get_bulk_upsert_object(
            object_id=2, object_type="composite", object_data=get_composite_data(subobjects=[])
        )],
        deleted_object_ids=[1]
    )
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200

    # Check if object was deleted
    db_cursor.execute("SELECT object_id FROM objects WHERE object_id = 1")
    assert not db_cursor.fetchone()


async def test_fully_delete_objects_which_are_not_subobjects_of_other_objects(cli, db_cursor):
    # Insert existing object
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(1)], db_cursor)

    body = get_bulk_upsert_request_body(
        objects=[get_bulk_upsert_object()],
        deleted_object_ids=[1]
    )
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200

    # Check if object was deleted
    db_cursor.execute("SELECT object_id FROM objects WHERE object_id = 1")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
