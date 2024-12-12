if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object
from tests.data_generators.tags import get_test_tag
from tests.data_generators.users import get_test_user

from tests.data_sets.tags import tag_list

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags
from tests.db_operations.users import insert_users

from tests.util import ensure_equal_collection_elements


async def test_view_existing_tags(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)

    # Correct request
    tag_ids = [tag["tag_id"] for tag in tag_list]
    resp = await cli.post("/tags/view", json={"tag_ids": tag_ids})
    assert resp.status == 200
    data = await resp.json()
    assert "tags" in data

    # Check if only published tags are returned
    expected_ids = [tag["tag_id"] for tag in tag_list if tag["is_published"]]
    assert len(expected_ids) < len(tag_ids) # ensure there are non-published tags in the fixture
    ensure_equal_collection_elements(expected_ids, [data["tags"][x]["tag_id"] for x in range(len(data["tags"]))], 
        "Tags view, correct request")
        
    for field in ("tag_id", "tag_name", "tag_description", "created_at", "modified_at", "is_published"):
        assert field in data["tags"][0]


async def test_view_object_ids_of_tags(cli, db_cursor):
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

if __name__ == "__main__":
    run_pytest_tests(__file__)
