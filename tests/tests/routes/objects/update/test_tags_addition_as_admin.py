"""
Tests for object tagging in /objects/add route as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_object_attrs, get_test_object_data
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.db_operations.objects import insert_objects, insert_links
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags


async def test_incorrect_request_body(cli, db_cursor):
    insert_objects([get_object_attrs(1, object_name="old name")], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)

    # Incorrect added tags & items types & values
    for added_tags in [None, False, "not a list", 1, {}, [""], ["a" * 256], [-1], [0]]:
        obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
        obj["added_tags"] = added_tags
        resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Too many added tags
    obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
    obj["added_tags"] = ["a"] * 101
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 400


async def test_non_existing_tag_ids(cli, db_cursor):
    insert_objects([get_object_attrs(1, object_name="old name")], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(1)], db_cursor)

    # Try to update an object & add non-existing tag IDs
    obj = get_test_object(1, object_name="new name", pop_keys=["created_at", "modified_at", "object_type"])
    obj["added_tags"] = [1, 2, 3]
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute(f"SELECT object_name FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == "old name"

    db_cursor.execute(f"SELECT object_id FROM objects_tags WHERE object_id = 1")
    assert not db_cursor.fetchone()


async def test_empty_added_tags(cli, db_cursor):
    insert_objects([get_object_attrs(1, object_name="old name")], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)

    obj = get_test_object(1, object_name="new name", pop_keys=["created_at", "modified_at", "object_type"])
    obj["added_tags"] = []
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    db_cursor.execute(f"SELECT object_name FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == "new name"

    db_cursor.execute(f"SELECT object_id FROM objects_tags WHERE object_id = 1")
    assert not db_cursor.fetchone()


async def test_add_string_tags(cli, db_cursor):
    insert_objects([get_object_attrs(1, object_name="old name")], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([
        get_test_tag(1, tag_name="tag 1"),
        get_test_tag(2, tag_name="tag 2"),
        get_test_tag(3, tag_name="tag 3"),
        get_test_tag(4, tag_name="tag 4")
    ], db_cursor, generate_ids=True)
    insert_objects_tags([1], [4], db_cursor)

    # Update an object with existing & non-existing tags and their duplicates
    obj = get_test_object(1, object_name="new name", pop_keys=["created_at", "modified_at", "object_type"])
    obj["added_tags"] = [
        "New tag",                          # new tag
        "Duplicate tag", "DUPLICATE TAG",   # new tag passed twice
        "Tag 1",            # existing tag name as string
        "Tag 2", "TAG 2",   # duplicate existing tag name as string
        "Tag 3", 3          # existing tag name & its tag ID
    ]
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 3, 5, 6]     # 4 was previously tagged & was not in the request

    db_cursor.execute(f"SELECT object_name FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == "new name"

    # Check added objects' tags
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 6]

    # Check if new tags were added & is_published is set to true
    db_cursor.execute(f"SELECT tag_id, is_published FROM tags WHERE tag_name IN ('New tag', 'Duplicate tag')")
    assert [r[0] for r in db_cursor.fetchall()] == [5, 6]
    assert all((r[1] for r in db_cursor.fetchall()))


async def test_add_numeric_tag_ids(cli, db_cursor):
    insert_objects([get_object_attrs(1, object_name="old name")], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1], [4], db_cursor)

    # Update an object with existing tag IDs (and check duplicate processing)
    obj = get_test_object(1, object_name="new name", pop_keys=["created_at", "modified_at", "object_type"])
    obj["added_tags"] = [1, 2, 3, 2, 3]
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 3]

    db_cursor.execute(f"SELECT object_name FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == "new name"

    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4]


if __name__ == "__main__":
    run_pytest_tests(__file__)
