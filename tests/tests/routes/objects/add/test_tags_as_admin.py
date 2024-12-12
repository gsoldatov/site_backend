"""
Tests for object tagging in /objects/add route as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.tags import tag_list

from tests.db_operations.tags import insert_tags


async def test_objects_add_route(cli, db_cursor):
    # Insert mock data
    insert_tags(tag_list, db_cursor, generate_ids=True)

    # Incorrect object's tags
    for added_tags in ["not a list", 1, {}]:
        link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
        link["added_tags"] = added_tags
        resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
        assert resp.status == 400

    # Add non-existing tag by tag_id (and get a 400 error)
    link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    link["added_tags"] = [1, 100]
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 400

    # Add existing tags by tag_id and tag_name (and check duplicate tag_ids handling)
    link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
    link["added_tags"] = ["a0", 1, "b1", 2, 9, 10]
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 9, 10] # "a0", "b1", 9, 10
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 9, 10]
    
    # Add non-existing tags by tag_name (and check duplicate tag_name handling)
    link = get_test_object(2, pop_keys=["object_id", "created_at", "modified_at"])
    link["added_tags"] = ["a0", 2, 3, 4, "New Tag", "New Tag 2", "new tag"]
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [1, 2, 3, 4, 11, 12] # "a0", 2, 3, 4, "new tag", "new tag 2"
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 11, 12]
    db_cursor.execute(f"SELECT tag_name FROM tags WHERE tag_name = 'New Tag' OR tag_name = 'New Tag 2'")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == ["New Tag", "New Tag 2"]

    # Check if added new tags are published by default
    db_cursor.execute(f"SELECT COUNT(*) FROM tags WHERE tag_id IN (11, 12) AND is_published = TRUE")
    assert db_cursor.fetchone() == (2,)


if __name__ == "__main__":
    run_pytest_tests(__file__)
