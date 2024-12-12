"""
Tests for object tagging in /objects/update route as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_test_object_data
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.tags import tag_list

from tests.db_operations.objects import insert_objects, insert_links
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags


async def test_objects_update_route(cli, db_cursor):
    # Insert mock data
    insert_tags(tag_list, db_cursor, generate_ids=True)
    insert_objects([get_test_object(1, owner_id=1, pop_keys=["object_data"])], db_cursor)    
    l_list = [get_test_object_data(1)]
    insert_links(l_list, db_cursor)

    insert_objects_tags([1], [1, 2, 3, 4, 5], db_cursor)
    
    # Incorrect added_tags and removed_tag_ids
    for added_tags in ["not a list", 1, {}]:
        link = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
        link["added_tags"] = added_tags
        resp = await cli.put("/objects/update", json={"object": link}, headers=headers_admin_token)
        assert resp.status == 400
    
    for removed_tag_ids in ["not a list", 1, {}]:
        link = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
        link["removed_tag_ids"] = removed_tag_ids
        resp = await cli.put("/objects/update", json={"object": link}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Add non-existing tag by tag_id (and get a 400 error)
    link = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
    link["added_tags"] = [1, 100]
    resp = await cli.put("/objects/update", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 400

    # Add existing tags by tag_id and tag_name (check duplicates in request handling (added once) and retagging with the same tags (tag is reapplied))
    link = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
    link["added_tags"] = ["a0", "A0", 1, "B1", "i0", "I0", 10]
    resp = await cli.put("/objects/update", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 9, 10] # "i0", 10 were added; 1, 2 ("a0", "b1") were reapplied 
                                                  # (and should be returned for the case with partially applied tags in route with multiple objects being tagged)
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 9, 10]

    # Add non-existing tags by tag_name (and check duplicate tag_name handling) + remove existing tags
    link = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
    link["added_tags"] = ["a0", 2, "New Tag", "New Tag 2", "new tag"]
    link["removed_tag_ids"] = [9, 10]
    resp = await cli.put("/objects/update", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [1, 2, 11, 12] # 1, 2 were reapplied; "New Tag", "New Tag 2"
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 11, 12] # 9, 10 were removed; 11, 12 were added
    db_cursor.execute(f"SELECT tag_name FROM tags WHERE tag_name = 'New Tag' OR tag_name = 'New Tag 2'")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == ["New Tag", "New Tag 2"]

    # Check if added new tags are published by default
    db_cursor.execute(f"SELECT COUNT(*) FROM tags WHERE tag_id IN (11, 12) AND is_published = TRUE")
    assert db_cursor.fetchone() == (2,)

    # Add tags only
    link = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
    link["added_tags"] = ["a0", 2, 6, "New Tag 3"]
    resp = await cli.put("/objects/update", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [1, 2, 6, 13] # 1, 2 were reapplied; 6 and 13 were added
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 6, 11, 12, 13] # 6 and 13 were added

    # Remove tags only
    link = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
    link["removed_tag_ids"] = [11, 12, 13]
    resp = await cli.put("/objects/update", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    removed_tag_ids = data.get("object", {}).get("tag_updates", {}).get("removed_tag_ids")
    assert sorted(removed_tag_ids) == [11, 12, 13]
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 6]


if __name__ == "__main__":
    run_pytest_tests(__file__)
