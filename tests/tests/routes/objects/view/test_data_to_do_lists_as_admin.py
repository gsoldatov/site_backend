"""
Tests for operations with to-do lists performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests


from tests.data_generators.objects import get_test_object, get_object_attrs, \
    get_test_object_data, get_objects_attributes_list
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.objects import to_do_lists_data_list, \
    insert_data_for_view_tests_objects_with_non_published_tags

from tests.db_operations.objects import insert_objects, insert_to_do_lists

from tests.request_generators.objects import get_objects_view_request_body


async def test_view_non_existing_objects_data(cli):
    body = get_objects_view_request_body(object_ids=[], object_data_ids=[999, 1000])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 404


async def test_response_objects_data(cli, db_cursor):
    insert_objects([get_object_attrs(1, object_type="to_do_list")], db_cursor)
    to_do_list_id_and_data = get_test_object_data(1, object_type="to_do_list")
    insert_to_do_lists([to_do_list_id_and_data], db_cursor)

    # Check if object data is correctly returned
    body = get_objects_view_request_body(object_ids=[], object_data_ids=[1])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    objects_data = data["objects_data"]
    assert len(objects_data) == 1
    assert objects_data[0]["object_id"] == 1
    assert objects_data[0]["object_type"] == "to_do_list"
    
    expected_object_data = to_do_list_id_and_data["object_data"]
    received_object_data = objects_data[0]["object_data"]
    assert received_object_data["sort_type"] == expected_object_data["sort_type"]
    assert received_object_data["items"] == expected_object_data["items"]


async def test_view_non_published_objects(cli, db_cursor):
    # Insert mock values
    insert_objects(get_objects_attributes_list(21, 30), db_cursor)
    insert_to_do_lists(to_do_lists_data_list, db_cursor)

    # Check if data is returned for all objects
    object_data_ids = [_ for _ in range(21, 31)]
    body = get_objects_view_request_body(object_ids=[], object_data_ids=object_data_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    
    # Check to-do list's general object data attributes
    for k in ["sort_type", "items"]:
        assert k in data["objects_data"][0]["object_data"]
    
    # Check to-do list's item attributes
    for k in get_test_object(7, object_type="to_do_list")["object_data"]["items"][0].keys():
        assert k in data["objects_data"][0]["object_data"]["items"][0]
    
    # Check if data is returned for all objects
    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    assert sorted(object_data_ids) == sorted(received_objects_data_ids)


async def test_view_objects_with_non_published_tags(cli, db_cursor):
    # Insert data (published objects with published & non-published tags)
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor, object_type="to_do_list")
    requested_object_ids = inserts["inserted_object_ids"]

    # Check if data is returned for all objects
    body = get_objects_view_request_body(object_ids=[], object_data_ids=requested_object_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    assert sorted(requested_object_ids) == sorted(received_objects_data_ids)


if __name__ == "__main__":
    run_pytest_tests(__file__)
