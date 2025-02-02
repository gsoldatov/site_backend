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
    insert_tags([get_test_tag(1)], db_cursor)

    # Incorrect removed tags & items types & values
    for removed_tag_ids in ["not a list", 1, {}, ["a"], [-1], [0]]:
        obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
        obj["removed_tag_ids"] = removed_tag_ids
        resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Too many removed tags
    obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
    obj["removed_tag_ids"] = [1] * 101
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 400


async def test_non_existing_tag_ids(cli, db_cursor):
    insert_objects([get_object_attrs(1, object_name="old name")], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 3)], db_cursor)
    insert_objects_tags([1], [1, 2], db_cursor)

    # Update an object & remove non-existing tag IDs
    obj = get_test_object(1, object_name="new name", pop_keys=["created_at", "modified_at", "object_type"])
    obj["removed_tag_ids"] = [2, 3, 4]
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    assert data["object"]["tag_updates"]["removed_tag_ids"] == [2, 3, 4]

    db_cursor.execute(f"SELECT object_name FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == "new name"

    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert [r[0] for r in db_cursor.fetchall()] == [1]


async def test_remove_numeric_tag_ids(cli, db_cursor):
    insert_objects([get_object_attrs(1, object_name="old name")], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1], [1, 2, 3, 4], db_cursor)

    # Update an object & remove existing tag IDs (and check duplicate processing)
    obj = get_test_object(1, object_name="new name", pop_keys=["created_at", "modified_at", "object_type"])
    obj["removed_tag_ids"] = [2, 3, 4, 3, 4]
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    removed_tag_ids = data.get("object", {}).get("tag_updates", {}).get("removed_tag_ids")
    assert sorted(removed_tag_ids) == [2, 3, 4]

    db_cursor.execute(f"SELECT object_name FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == "new name"

    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert [r[0] for r in db_cursor.fetchall()] == [1]


async def test_add_and_remove_tags(cli, db_cursor):
    insert_objects([get_object_attrs(1, object_name="old name")], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1], [1, 2], db_cursor)

    # Update an object and add & remove tags at the same time
    obj = get_test_object(1, object_name="new name", pop_keys=["created_at", "modified_at", "object_type"])
    obj["added_tags"] = [3, 4, "New tag"]
    obj["removed_tag_ids"] = [1, 2, 100]
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    assert sorted(data["object"]["tag_updates"]["added_tag_ids"]) == [3, 4, 5]
    assert sorted(data["object"]["tag_updates"]["removed_tag_ids"]) == [1, 2, 100]

    db_cursor.execute(f"SELECT object_name FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone()[0] == "new name"

    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [3, 4, 5]


if __name__ == "__main__":
    run_pytest_tests(__file__)
