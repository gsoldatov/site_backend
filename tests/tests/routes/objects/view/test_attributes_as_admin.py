from datetime import datetime, timezone, timedelta

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.objects import insert_data_for_view_tests_non_published_objects, insert_data_for_view_tests_objects_with_non_published_tags

from tests.db_operations.objects import insert_objects

from tests.request_generators.objects import get_objects_view_request_body

from tests.util import ensure_equal_collection_elements


async def test_incorrect_request_body(cli):
    # Invalid JSON
    resp = await cli.post("/objects/view", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Missing and unallowed attributes
    for attr in ("object_ids", "object_data_ids"):
        body = get_objects_view_request_body(object_data_ids=[1])
        body.pop(attr)
        resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    body = get_objects_view_request_body()
    body["unallowed"] = 1
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect attribute values
    incorrect_attributes = {
        "object_ids": [None, 1, "a", False, {}, ["a"], [-1], [0], [1] * 1001],
        "object_data_ids": [None, 1, "a", False, {}, ["a"], [-1], [0], [1] * 1001]
    }
    for attr, values in incorrect_attributes.items():
        for value in values:
            body = get_objects_view_request_body()
            body[attr] = value
            resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
            assert resp.status == 400
    
    # Both lists are empty
    body = get_objects_view_request_body(object_ids=[], object_data_ids=[])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 400
    

async def test_view_non_existing_objects_attributes(cli):
    body = get_objects_view_request_body(object_ids=[999, 1000], object_data_ids=[])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 404


async def test_response_objects_attributes(cli, db_cursor):
    now = datetime.now(tz=timezone.utc)
    objects_map = {
        1: get_test_object(1, created_at=now - timedelta(days=1), owner_id=1, pop_keys=["object_data"]),
        2: get_test_object(2, object_type="markdown", created_at=now - timedelta(days=2),
                           feed_timestamp=now - timedelta(days=5), owner_id=1, pop_keys=["object_data"])
    }
    insert_objects(objects_map.values(), db_cursor)

    body = get_objects_view_request_body(object_ids=[1, 2], object_data_ids=[])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    
    # Check if object attributes are correctly returned
    assert resp.status == 200
    data = await resp.json()
    response_objects = data["objects_attributes_and_tags"]
    assert len(response_objects) == 2

    for obj in response_objects:
        object_id = obj["object_id"]
        for attr in ("object_type", "object_name", "object_description",
                     "is_published", "display_in_feed", "show_description"):
            assert objects_map[object_id][attr] == obj[attr]

        assert datetime.fromisoformat(objects_map[object_id]["created_at"]) == datetime.fromisoformat(obj["created_at"])
        assert datetime.fromisoformat(objects_map[object_id]["modified_at"]) == datetime.fromisoformat(obj["modified_at"])

        if object_id == 2:
            assert datetime.fromisoformat(objects_map[object_id]["feed_timestamp"]) == datetime.fromisoformat(obj["feed_timestamp"])
        else:
            assert obj["feed_timestamp"] == None


async def test_view_non_published_objects(cli, db_cursor):
    # Insert mock values
    inserts = insert_data_for_view_tests_non_published_objects(db_cursor)
    expected_object_ids = inserts["inserted_object_ids"]
    
    # Check if correct object IDs are returned in objects attributes
    body = get_objects_view_request_body(object_ids=expected_object_ids, object_data_ids=[])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()

    received_object_ids = [data["objects_attributes_and_tags"][x]["object_id"] for x in range(len(data["objects_attributes_and_tags"]))]
    ensure_equal_collection_elements(expected_object_ids, received_object_ids,
        "Objects view, correct request as admin, object_ids only")
    
    # Check if correct object IDs are returned in objects attributes and data
    # NOTE: object_data_ids only case is checked type-specific tests
    object_ids = [_ for _ in range(1, 6)]
    object_data_ids = [_ for _ in range(6, 11)]
    body = get_objects_view_request_body(object_ids=object_ids, object_data_ids=object_data_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    for attr in ("objects_attributes_and_tags", "objects_data"):
        assert attr in data
    
    received_object_ids = [data["objects_attributes_and_tags"][x]["object_id"] for x in range(len(data["objects_attributes_and_tags"]))]
    ensure_equal_collection_elements(object_ids, received_object_ids, 
        "Objects view, correct request for both object attributes and data as admin, object_ids")
    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    ensure_equal_collection_elements(object_data_ids, received_objects_data_ids,
        "Objects view, correct request for both object attributes and data as admin, object_data_ids")


async def test_view_objects_with_non_published_tags(cli, db_cursor):
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor)
    object_ids = inserts["inserted_object_ids"]

    # Check if correct object IDs are returned in objects attributes
    body = get_objects_view_request_body(object_ids=object_ids, object_data_ids=[])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()

    received_object_ids = [data["objects_attributes_and_tags"][x]["object_id"] for x in range(len(data["objects_attributes_and_tags"]))]
    ensure_equal_collection_elements(object_ids, received_object_ids, 
        "Objects view, correct request as admin, object_ids only")
    
    # Check if correct object IDs are returned in objects attributes and data
    # NOTE: object_data_ids only case is checked type-specific tests
    object_ids = [1, 3, 5, 7, 9]
    object_data_ids = [2, 4, 6, 8, 10]
    body = get_objects_view_request_body(object_ids=object_ids, object_data_ids=object_data_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    
    received_object_ids = [data["objects_attributes_and_tags"][x]["object_id"] for x in range(len(data["objects_attributes_and_tags"]))]
    ensure_equal_collection_elements(object_ids, received_object_ids, 
        "Objects view, correct request for both object attributes and data as admin, object_ids")
    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    ensure_equal_collection_elements(object_data_ids, received_objects_data_ids, 
        "Objects view, correct request for both object attributes and data as admin, object_data_ids")


if __name__ == "__main__":
    run_pytest_tests(__file__)
