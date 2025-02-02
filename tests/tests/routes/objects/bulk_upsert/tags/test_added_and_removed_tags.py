"""
Tests for simultaneous tag addition & removal in /objects/upsert route.
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


async def test_add_and_remove_the_same_tag(cli, db_cursor):#
    # Insert an object and tags
    insert_objects([get_object_attrs(1)], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1], [1, 2], db_cursor)

    # Update the object
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1, added_tags=[2, 3], removed_tag_ids=[1, 3])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    ## 1 was removed; 2 was added; 3 was added and then removed
    assert sorted(data["objects_attributes_and_tags"][0]["current_tag_ids"]) == [2]

    # Check database
    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [2]


async def test_add_and_remove_tags(cli, db_cursor):
    # Insert objects and their tags
    insert_objects([get_object_attrs(i) for i in range(1, 3)], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(i) for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1, 2], db_cursor)

    # Update existing objects & add new objects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=1, added_tags=[3, 4, "a"], removed_tag_ids=[1, 2]),
        get_bulk_upsert_object(object_id=2, added_tags=[3, "a", "b"], removed_tag_ids=[1]),
        get_bulk_upsert_object(object_id=0, added_tags=[1, 2, "a", "c"]),
        get_bulk_upsert_object(object_id=-1, added_tags=[3, 4, "b", "c"])
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
     
    # Check database
    ## New tags were added
    db_cursor.execute("SELECT tag_id, tag_name FROM tags WHERE tag_name IN ('a', 'b', 'c')")
    name_id_map = {r[1]: r[0] for r in db_cursor.fetchall()}
    a_id, b_id, c_id = name_id_map["a"], name_id_map["b"], name_id_map["c"]
    assert sorted(name_id_map.values()) == [5, 6, 7]

    ## Check objects tags
    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted(r[0] for r in db_cursor.fetchall()) == sorted([3, 4, a_id])
    
    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 2")
    assert sorted(r[0] for r in db_cursor.fetchall()) == sorted([2, 3, a_id, b_id])

    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 3")
    assert sorted(r[0] for r in db_cursor.fetchall()) == sorted([1, 2, a_id, c_id])

    db_cursor.execute("SELECT tag_id FROM objects_tags WHERE object_id = 4")
    assert sorted(r[0] for r in db_cursor.fetchall()) == sorted([3, 4, b_id, c_id])

    # Check response
    assert resp.status == 200
    data = await resp.json()

    sorted_current_tag_ids = [
        sorted(o["current_tag_ids"]) for o in
        (sorted((o for o in data["objects_attributes_and_tags"]), key=lambda x: x["object_id"]))
    ]
    assert sorted_current_tag_ids == [
        sorted([3, 4, a_id]),
        sorted([2, 3, a_id, b_id]),
        sorted([1, 2, a_id, c_id]),
        sorted([3, 4, b_id, c_id])
    ]


if __name__ == "__main__":
    run_pytest_tests(__file__)
