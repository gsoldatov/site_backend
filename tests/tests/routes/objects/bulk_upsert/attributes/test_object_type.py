"""
Tests for `object_type` attribute in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from typing import get_args

from backend_main.types.domains.objects.attributes import ObjectType

from tests.data_generators.objects import get_object_attrs
from tests.data_generators.sessions import headers_admin_token
from tests.db_operations.objects import insert_objects
from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_values(cli, db_cursor):
    # Missing attribute
    body = get_bulk_upsert_request_body()
    body["objects"][0].pop("object_type")
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    for value in [None, False, "wrong str", {}, [], [1]]:
        body = get_bulk_upsert_request_body()
        body["objects"][0]["object_type"] = value
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_try_changing_object_type(cli, db_cursor):
    # Insert objects into the database
    insert_objects([
        get_object_attrs(1, object_type="link"),
        get_object_attrs(2, object_type="markdown"),
        get_object_attrs(3, object_type="to_do_list"),
        get_object_attrs(4, object_type="composite")
    ], db_cursor, generate_ids=True)

    # Try updating object type for each object type
    object_types = get_args(ObjectType)
    object_ids_and_types = ((i + 1, t) for i, t in enumerate(object_types))

    for object_id, current_type in object_ids_and_types:
        for object_type in object_types:
            if object_type != current_type:
                body = get_bulk_upsert_request_body(objects=[
                    get_bulk_upsert_object(object_id=object_id, object_type=object_type)
                ])
                resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
                assert resp.status == 400


async def test_add_new_objects(cli, db_cursor):
    # Insert an object (acts as a composite subobject)
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)

    # Add new objects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_type="link"),
        get_bulk_upsert_object(object_id=-1, object_type="markdown"),
        get_bulk_upsert_object(object_id=-2, object_type="to_do_list"),
        get_bulk_upsert_object(object_id=-3, object_type="composite")
    ])
    assert len(get_args(ObjectType)) == len(body["objects"]), "Add missing object type here"
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    sorted_attrs = sorted((o for o in data["objects_attributes_and_tags"]), key=lambda o: o["object_id"])
    assert [o["object_id"] for o in sorted_attrs] == [2, 3, 4, 5]
    assert [o["object_type"] for o in sorted_attrs] == ["link", "markdown", "to_do_list", "composite"]

    # Check database
    db_cursor.execute("SELECT object_id, object_type FROM objects WHERE object_id IN (2, 3, 4, 5)")
    rows = [r for r in db_cursor.fetchall()]
    sorted_ids_and_types = [(r[0], r[1]) for r in sorted(rows, key=lambda x: x[0])]
    assert sorted_ids_and_types == [(2, "link"), (3, "markdown"), (4, "to_do_list"), (5, "composite")]


async def test_update_objects(cli, db_cursor):
    # Insert objects into the database
    insert_objects([
        get_object_attrs(1, object_type="link"),
        get_object_attrs(2, object_type="markdown"),
        get_object_attrs(3, object_type="to_do_list"),
        get_object_attrs(4, object_type="composite")
    ], db_cursor, generate_ids=True)

    # Update objects without changing their `object_type`
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1, object_type="link"),
        get_bulk_upsert_object(object_id=2, object_type="markdown"),
        get_bulk_upsert_object(object_id=3, object_type="to_do_list"),
        get_bulk_upsert_object(object_id=4, object_type="composite")
    ])
    assert len(get_args(ObjectType)) == len(body["objects"]), "Add missing object type here"
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    sorted_attrs = sorted((o for o in data["objects_attributes_and_tags"]), key=lambda o: o["object_id"])
    assert [o["object_id"] for o in sorted_attrs] == [1, 2, 3, 4]
    assert [o["object_type"] for o in sorted_attrs] == ["link", "markdown", "to_do_list", "composite"]

    # Check database
    db_cursor.execute("SELECT object_id, object_type FROM objects WHERE object_id IN (1, 2, 3, 4)")
    rows = [r for r in db_cursor.fetchall()]
    sorted_ids_and_types = [(r[0], r[1]) for r in sorted(rows, key=lambda x: x[0])]
    assert sorted_ids_and_types == [(1, "link"), (2, "markdown"), (3, "to_do_list"), (4, "composite")]


if __name__ == "__main__":
    run_pytest_tests(__file__)
