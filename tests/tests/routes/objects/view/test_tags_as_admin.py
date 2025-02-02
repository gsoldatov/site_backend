"""
Tests for viewing objects' tags in /objects/view route as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.objects import insert_data_for_view_tests_objects_with_non_published_tags
from tests.data_sets.tags import tag_list

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags

from tests.request_generators.objects import get_objects_view_request_body


async def test_objects_view_route(cli, db_cursor):
    # Insert mock data
    insert_tags(tag_list, db_cursor, generate_ids=True)
    objects = [get_object_attrs(i) for i in range(1, 4)]
    insert_objects(objects, db_cursor)
    objects_tags = {1: [1, 2, 3], 2: [3, 4, 5]}
    insert_objects_tags([1], objects_tags[1], db_cursor)
    insert_objects_tags([2], objects_tags[2], db_cursor)

    # View object without tags
    object_ids = [3]
    body = get_objects_view_request_body(object_ids=object_ids, object_data_ids=[])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert type(data.get("objects_attributes_and_tags")) == list
    assert len(data.get("objects_attributes_and_tags")) == 1
    assert type(data["objects_attributes_and_tags"][0]) == dict
    current_tag_ids = data["objects_attributes_and_tags"][0].get("current_tag_ids")
    assert type(current_tag_ids) == list
    assert len(current_tag_ids) == 0

    # View objects with tags
    object_ids = [1, 2]
    body = get_objects_view_request_body(object_ids=object_ids, object_data_ids=[])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    for i in range(2):
        obj = data["objects_attributes_and_tags"][i]
        assert sorted(obj["current_tag_ids"]) == sorted(objects_tags[obj["object_id"]])


async def test_objects_view_route_objects_with_non_published_tags(cli, db_cursor):
    # Insert data
    insert_data_for_view_tests_objects_with_non_published_tags(db_cursor)

    # View objects' tags for objects with non-published tags
    body = get_objects_view_request_body(object_ids=[6, 10], object_data_ids=[])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()

    # Check if both objects are returned with expected tags
    assert len(data["objects_attributes_and_tags"]) == 2
    for i in range(2):
        assert (data["objects_attributes_and_tags"][i]["object_id"] == 6 and sorted(data["objects_attributes_and_tags"][i]["current_tag_ids"]) == [1, 2, 3]) \
            or (data["objects_attributes_and_tags"][i]["object_id"] == 10 and sorted(data["objects_attributes_and_tags"][i]["current_tag_ids"]) == [1, 2, 3, 4])


if __name__ == "__main__":
    run_pytest_tests(__file__)
