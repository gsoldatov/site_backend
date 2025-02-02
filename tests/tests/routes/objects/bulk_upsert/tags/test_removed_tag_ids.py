"""
Tests for `removed_tag_ids` attribute in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs, get_test_object_data
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.db_operations.objects import insert_objects, insert_links
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_request_body(cli, db_cursor):
    # Insert an object & its tags
    insert_objects([get_object_attrs(1)], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(1)], db_cursor)
    insert_objects_tags([1], [1], db_cursor)

    # Missing attribute
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1)
    ])
    body["objects"][0].pop("removed_tag_ids")
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect added tags & items types & values
    for removed_tag_ids in [None, "not a list", 1, {}, [""], [-1], [0], [1] * 101]:
        body = get_bulk_upsert_request_body()
        body["objects"][0]["removed_tag_ids"] = removed_tag_ids
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_shared_removed_tag_ids_limit(cli, db_cursor):
    # Insert objects & their tags
    insert_objects([get_object_attrs(i) for i in range(1, 21)], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(1)], db_cursor)
    insert_objects_tags([i for i in range(1, 21)], [1], db_cursor)

    # Update an object
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=i, removed_tag_ids=[1] * 51)
    for i in range(1, 21)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_remove_non_existing_tags(cli, db_cursor):
    # Insert an object & its tags
    insert_objects([get_object_attrs(1)], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(1)], db_cursor)
    insert_objects_tags([1], [1], db_cursor)

    # Update an object
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1, removed_tag_ids=[999])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["current_tag_ids"] == [1]

    # Check database
    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert [r[0] for r in db_cursor.fetchall()] == [1]


async def test_remove_tag_ids_of_a_new_object(cli, db_cursor):
    insert_tags([get_test_tag(1)], db_cursor)
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, removed_tag_ids=[1])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["current_tag_ids"] == []

    # Check database
    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert not db_cursor.fetchone()


async def test_add_an_object_with_empty_removed_tag_ids(cli, db_cursor):
    # Insert an object & its tags
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(1)], db_cursor)
    insert_objects_tags([1], [1], db_cursor)

    # Update an object
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, removed_tag_ids=[])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["current_tag_ids"] == []

    # Check database
    db_cursor.execute("SELECT object_id, tag_id FROM objects_tags")
    assert [r for r in db_cursor.fetchall()] == [(1, 1)]


async def test_update_an_object_with_empty_removed_tag_ids(cli, db_cursor):
    # Insert an object & its tags
    insert_objects([get_object_attrs(1)], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(1)], db_cursor)
    insert_objects_tags([1], [1], db_cursor)
    
    # Update an object
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1, removed_tag_ids=[])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["current_tag_ids"] == [1]

    # Check database
    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert [r[0] for r in db_cursor.fetchall()] == [1]


async def test_remove_non_applied_tags(cli, db_cursor):
    # Insert an object & its tags
    insert_objects([get_object_attrs(1)], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 4)], db_cursor)
    insert_objects_tags([1], [1, 2], db_cursor)

    # Update an object
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1, removed_tag_ids=[3])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["current_tag_ids"] == [1, 2]

    # Check database
    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [1, 2]


async def test_update_objects_and_remove_tag_ids(cli, db_cursor):#
    # Insert objects and their tags
    insert_objects([get_object_attrs(i) for i in range(1, 4)], db_cursor)
    insert_links([get_test_object_data(i) for i in range(1, 4)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2, 3], [1, 2, 3, 4], db_cursor)

    # Update objects & check duplicate handling
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=i, removed_tag_ids=[2, 3, 4, 3, 4])
     for i in range(1, 3)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert data["objects_attributes_and_tags"][0]["current_tag_ids"] == [1]
    assert data["objects_attributes_and_tags"][1]["current_tag_ids"] == [1]

    # Check database
    ## Updated objects' tags
    db_cursor.execute("SELECT object_id, tag_id FROM objects_tags WHERE object_id IN (1, 2)")
    received_objects_tags = sorted((r for r in db_cursor.fetchall()), key=lambda x: x[0])
    assert received_objects_tags == [(1, 1), (2, 1)]

    ## Tags of an object, which was not updated
    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 3")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [1, 2, 3, 4]


if __name__ == "__main__":
    run_pytest_tests(__file__)
