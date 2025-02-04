if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_objects_attributes_list
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.data_sets.tags import tag_list

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags


async def test_incorrect_request_body(cli):
    # Invalid JSON
    resp = await cli.post("/tags/view", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Missing required attributes
    resp = await cli.post("/tags/view", json={}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect & unallowed attributes
    incorrect_attributes = {
        "tag_ids": [None, False, "str", 1, {}, ["a"], [], [-1], [1] * 1001],
        "unallowed": ["unallowed"]
    }
    for attr, values in incorrect_attributes.items():
        for value in values:
            body = {"tag_ids": [1]}
            body[attr] = value
            resp = await cli.post("/tags/view", json=body, headers=headers_admin_token)
            assert resp.status == 400


async def test_view_non_existing_tags(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)
    
    resp = await cli.post("/tags/view", json={"tag_ids": [999, 1000]}, headers=headers_admin_token)
    assert resp.status == 404


async def test_view_existing_tags(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)

    # Correct request
    tag_ids = [tag["tag_id"] for tag in tag_list]
    resp = await cli.post("/tags/view", json={"tag_ids": tag_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "tags" in data

    # Check if both published and non-published tags are returned
    assert sorted(tag_ids) == sorted([data["tags"][x]["tag_id"] for x in range(len(data["tags"]))])
        
    for field in ("tag_id", "tag_name", "tag_description", "created_at", "modified_at", "tag_description"):
        assert field in data["tags"][0]

# # NOTE: `return_current_object_ids` option was removed & current object IDs are no longer returned
# async def test_view_object_ids_of_tags(cli, db_cursor):
#     # Insert mock data
#     tags = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
#     insert_tags(tags, db_cursor)
#     insert_objects(get_objects_attributes_list(1, 10), db_cursor)
#     tags_objects = {1: [1, 2, 3], 2: [3, 4, 5]}
#     insert_objects_tags(tags_objects[1], [1], db_cursor)
#     insert_objects_tags(tags_objects[2], [2], db_cursor)

#     # View tag without tagged objects
#     tag_ids = [3]
#     resp = await cli.post("/tags/view", json={"tag_ids": tag_ids, "return_current_object_ids": True}, headers=headers_admin_token)
#     assert resp.status == 200
#     data = await resp.json()
#     assert type(data.get("tags")) == list
#     assert len(data.get("tags")) == 1
#     assert type(data["tags"][0]) == dict
#     current_object_ids = data["tags"][0].get("current_object_ids")
#     assert type(current_object_ids) == list
#     assert len(current_object_ids) == 0

#     # View tags with tagged objects
#     tag_ids = [1, 2]
#     resp = await cli.post("/tags/view", json={"tag_ids": tag_ids, "return_current_object_ids": True}, headers=headers_admin_token)
#     assert resp.status == 200
#     data = await resp.json()
#     for i in range(2):
#         tag_data = data["tags"][i]
#         assert sorted(tag_data["current_object_ids"]) == sorted(tags_objects[tag_data["tag_id"]])


if __name__ == "__main__":
    run_pytest_tests(__file__)
