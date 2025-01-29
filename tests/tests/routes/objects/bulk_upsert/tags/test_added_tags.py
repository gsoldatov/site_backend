"""
Tests for `added_tags` attribute in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_test_object_data
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.db_operations.objects import insert_objects, insert_links
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_request_body(cli, db_cursor):    
    # Missing attribute
    body = get_bulk_upsert_request_body()
    body["objects"][0].pop("added_tags")
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect added tags & items types & values
    for added_tags in [None, "not a list", 1, {}, [""], ["a" * 256], [-1], [0], ["a"] * 101]:
        body = get_bulk_upsert_request_body()
        body["objects"][0]["added_tags"] = added_tags
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_shared_added_tags_limit(cli, db_cursor):
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=-i, added_tags=["a"] * 51)
    for i in range(20)])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_try_adding_non_existing_tag_ids(cli, db_cursor):
    insert_tags([get_test_tag(1)], db_cursor)

    # Try to update an object & add non-existing tag IDs
    body = get_bulk_upsert_request_body()
    body["objects"][0]["added_tags"] = [1, 2, 3]
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_a_new_object_without_added_tags(cli, db_cursor):
    # Try to update an object & add non-existing tag IDs
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object(added_tags=[])])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200

    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert not db_cursor.fetchone()


async def test_update_an_existing_object_without_added_tags(cli, db_cursor):
    # Insert an existing object & its tags
    insert_objects([get_test_object(1, owner_id=1, pop_keys=["object_data"])], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 4)], db_cursor)
    insert_objects_tags([1], [1, 2, 3], db_cursor)

    # Try to update an object & add non-existing tag IDs
    body = get_bulk_upsert_request_body(objects=[get_bulk_upsert_object(object_id=1, added_tags=[])])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200

    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [1, 2, 3]


async def test_update_an_existing_object_with_already_applied_tags(cli, db_cursor):
    # Insert an object & its tags
    insert_objects([get_test_object(1, owner_id=1, pop_keys=["object_data"])], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([
        get_test_tag(1, tag_name="tag 1"),
        get_test_tag(2, tag_name="tag 2")
    ], db_cursor)
    insert_objects_tags([1], [1, 2], db_cursor)

    # Update an object & apply tags for the second time
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1, added_tags=[1, "TAG 2"])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert sorted(data["objects_attributes_and_tags"][0]["current_tag_ids"]) == [1, 2]

    # Check database
    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [1, 2]


async def test_add_string_tags(cli, db_cursor):
    # Insert an object & its tags
    insert_objects([get_test_object(1, owner_id=1, pop_keys=["object_data"])], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([
        get_test_tag(1, tag_name="tag 1"),
        get_test_tag(2, tag_name="tag 2"),
        get_test_tag(3, tag_name="tag 3"),
        get_test_tag(4, tag_name="tag 4")
    ], db_cursor, generate_ids=True)
    insert_objects_tags([1], [4], db_cursor)

    # Upsert an existing & a new objects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1, added_tags=[
            "New tag",                          # new tag
            "Duplicate tag", "DUPLICATE TAG",   # new tag passed twice
            "Tag 1",                # existing tag name as string
            "Tag 2", "TAG 2",       # duplicate existing tag name as string
            "Tag 3", 3,             # existing tag name & its tag ID
            "Multitag duplicate"    # New tag added in two objects
        ]),
        get_bulk_upsert_object(object_id=0, added_tags=[
            "MULTITAG DUPLICATE"    # New tag added in two objects
        ])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check database
    ## Check if new tags were added & is_published is set to true
    db_cursor.execute(
        f"SELECT tag_id, tag_name, is_published FROM tags WHERE tag_name IN ('New tag', 'Duplicate tag', 'Multitag duplicate')"
    )
    rows = [r for r in db_cursor.fetchall()]
    assert [r[0] for r in rows] == [5, 6, 7]
    assert all((r[2] for r in rows))
    tag_name_to_id_map = {r[1]: r[0] for r in rows}
    multitag_duplicate_id = tag_name_to_id_map["Multitag duplicate"]

    ## Existing object
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 6, 7]

    ## New object
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 2")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [multitag_duplicate_id]

    # Check response
    assert resp.status == 200
    data = await resp.json()
    current_tag_ids = [sorted(
        o["current_tag_ids"]) for o in
        sorted((o for o in data["objects_attributes_and_tags"]), key=lambda x: x["object_id"])
    ]
    # 1-3 are existing added as sting tags
    # 4 was applied before the request
    # 5, 6, 7 - tags added during request (order is random)
    assert current_tag_ids == [[1, 2, 3, 4, 5, 6, 7], [multitag_duplicate_id]]
    
    
async def test_add_numeric_tag_ids(cli, db_cursor):
    # Insert an object & its tags
    insert_objects([get_test_object(1, owner_id=1, pop_keys=["object_data"])], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1], [4], db_cursor)

    # Upsert an existing & a new objects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1, added_tags=[1, 2, 3, 2, 3]),
        get_bulk_upsert_object(object_id=0, added_tags=[1, 2, 1, 2])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    current_tag_ids = [sorted(
        o["current_tag_ids"]) for o in
        sorted((o for o in data["objects_attributes_and_tags"]), key=lambda x: x["object_id"])
    ]
    # 4 was applied before the request
    assert current_tag_ids == [[1, 2, 3, 4], [1, 2]]
    
    # Check database
    ## Existing object
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4]

    ## New object
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 2")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2]


if __name__ == "__main__":
    run_pytest_tests(__file__)
