"""
Tests for object tagging in /objects/... and /tags/... routes performed as anonymous.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.objects import get_test_object
from tests.fixtures.data_generators.tags import get_test_tag
from tests.fixtures.data_generators.users import get_test_user

from tests.fixtures.db_operations.objects import insert_objects
from tests.fixtures.db_operations.objects_tags import insert_objects_tags
from tests.fixtures.db_operations.tags import insert_tags
from tests.fixtures.db_operations.users import insert_users


async def test_tags_view_route(cli, db_cursor):
    # Insert mock data
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user

    object_attributes = [get_test_object(i, owner_id=1 if i <= 2 else 2, is_published=i % 2 == 0, pop_keys=["object_data"]) for i in range(1, 5)]
    insert_objects(object_attributes, db_cursor)

    insert_tags([get_test_tag(1), get_test_tag(2)], db_cursor)

    insert_objects_tags([1, 2, 3, 4], [1], db_cursor)
    insert_objects_tags([1, 3], [2], db_cursor)
    
    # View tag with `return_current_object_ids` without any published objects tagged by it
    resp = await cli.post("/tags/view", json={"tag_ids": [2], "return_current_object_ids": True})
    assert resp.status == 200
    tag_data = (await resp.json())["tags"][0]
    assert tag_data["current_object_ids"] == []

    # View tag with `return_current_object_ids` with both published and non-published objects
    resp = await cli.post("/tags/view", json={"tag_ids": [1], "return_current_object_ids": True})
    assert resp.status == 200
    tag_data = (await resp.json())["tags"][0]
    assert sorted(tag_data["current_object_ids"]) == [2, 4]


async def test_objects_update_tags_route(cli, db_cursor):
    # Insert mock data
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user

    object_attributes = [get_test_object(i, owner_id=1 if i <= 1 else 2, pop_keys=["object_data"]) for i in range(1, 3)]
    insert_objects(object_attributes, db_cursor)

    tags = [get_test_tag(i) for i in range(1, 11)]
    insert_tags(tags, db_cursor)

    tags_objects = {1: [1, 2, 3, 4, 5], 2: [1, 2, 6, 7]}
    for k in tags_objects:
        insert_objects_tags([k], tags_objects[k], db_cursor)
        
    # Try to update objects tags with different parameters
    for updates in [{"object_ids": [1], "added_tags": [6, 7, 8, "New Tag"]},
        {"object_ids": [1], "removed_tag_ids": [1, 2, 3]},
        {"object_ids": [2], "added_tags": [4, 5, 8, "New Tag"]},
        {"object_ids": [2], "removed_tag_ids": [1, 2, 7]},]:
        resp = await cli.put("/objects/update_tags", json=updates)
        assert resp.status == 401


if __name__ == "__main__":
    run_pytest_tests(__file__)
