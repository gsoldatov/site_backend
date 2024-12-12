"""
Tests for object tagging in /objects/update_tags route as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from datetime import datetime

from tests.fixtures.data_generators.objects import get_objects_attributes_list
from tests.fixtures.data_generators.sessions import headers_admin_token

from tests.fixtures.data_sets.tags import tag_list

from tests.fixtures.db_operations.objects import insert_objects
from tests.fixtures.db_operations.objects_tags import insert_objects_tags
from tests.fixtures.db_operations.tags import insert_tags


async def test_objects_update_tags_route(cli, db_cursor):
    obj_list = get_objects_attributes_list(1, 10)

    # Insert mock values
    insert_tags(tag_list, db_cursor, generate_ids=True)
    insert_objects(obj_list, db_cursor)
    objects_tags = {1: [1, 2, 3], 2: [3, 4, 5]}
    insert_objects_tags([1], objects_tags[1], db_cursor)
    insert_objects_tags([2], objects_tags[2], db_cursor)

    # Incorrect attributes
    for attr in ["remove_all_tags", "tag_ids", "added_object_ids", "removed_object_ids"]:
        updates = {"object_ids": [1], "added_tags": [3, 4, 5, 6]}
        updates[attr] = [1, 2, 3]
        resp = await cli.put("/objects/update_tags", json=updates, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect parameter values
    for attr in ["object_ids", "added_tags", "removed_tag_ids"]:
        for incorrect_value in [1, "1", {}]:
            updates = {"object_ids": [1], "added_tags": [3, 4, 5, 6]}
            updates[attr] = incorrect_value
            resp = await cli.put("/objects/update_tags", json=updates, headers=headers_admin_token)
            assert resp.status == 400
    
    # Add non-existing tags by tag_id (and receive a 400 error)
    updates = {"object_ids": [1], "added_tags": [1, 100]}
    resp = await cli.put("/objects/update_tags", json=updates, headers=headers_admin_token)
    assert resp.status == 400

    # Update non-existing objects (and receive a 400 error)
    updates = {"object_ids": [1, 100], "added_tags": [3, 4, 5, 6]}
    resp = await cli.put("/objects/update_tags", json=updates, headers=headers_admin_token)
    assert resp.status == 400
    
    # Add new tags by tag_name and tag_ids (and check duplicate handling)
    updates = {"object_ids": [1], "added_tags": [4, 5, 6, "New Tag", 4, 5, "c0"]}
    resp = await cli.put("/objects/update_tags", json=updates, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [3, 4, 5, 6, 11] # c0 = 3; 11 was added for "New Tag"
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 6, 11]
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 2")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == sorted(objects_tags[2])
    assert data.get("tag_updates", {}).get("removed_tag_ids") == []

    # Check modified_at values for modfied and not modified objects
    # Response from server format: "2021-04-27T15:29:41.701892+00:00"
    # Cursor value format - datetime with timezone, converted to str: "2021-04-27 15:43:02.557558"
    db_cursor.execute(f"SELECT modified_at FROM objects WHERE object_id = 1")
    db_modified_at_value = db_cursor.fetchone()[0]
    assert db_modified_at_value == datetime.strptime(data["modified_at"], "%Y-%m-%dT%H:%M:%S.%f%z")

    db_cursor.execute(f"SELECT modified_at FROM objects WHERE object_id = 2")
    assert db_cursor.fetchone()[0] == obj_list[1]["modified_at"]

    # Remove tags by tag_id
    updates = {"object_ids": [1], "removed_tag_ids": [1, 2, 3]}
    resp = await cli.put("/objects/update_tags", json=updates, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data.get("tag_updates", {}).get("added_tag_ids") == []
    removed_tag_ids = data.get("tag_updates", {}).get("removed_tag_ids")
    assert sorted(removed_tag_ids) == [1, 2, 3]
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [4, 5, 6, 11] # 1, 2, 3 were removed
    
    # Add and remove tags simultaneously
    updates = {"object_ids": [1, 2], "added_tags": [1, 2, "New Tag 2"], "removed_tag_ids": [3, 4, 5]}
    resp = await cli.put("/objects/update_tags", json=updates, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [1, 2, 12] # 12 was added for "New Tag 2"
    removed_tag_ids = data.get("tag_updates", {}).get("removed_tag_ids")
    assert sorted(removed_tag_ids) == [3, 4, 5]
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 6, 11, 12] # 1, 2, 12 were added; 4, 5 were removed
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 2")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 12] # 1, 2 were added; 3, 4, 5 were removed


if __name__ == "__main__":
    run_pytest_tests(__file__)
