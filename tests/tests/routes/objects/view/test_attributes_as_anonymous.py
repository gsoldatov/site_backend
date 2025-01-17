if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_sets.objects import insert_data_for_view_tests_non_published_objects, insert_data_for_view_tests_objects_with_non_published_tags
from tests.request_generators.objects import get_objects_view_request_body
from tests.util import ensure_equal_collection_elements


async def test_view_non_published_objects(cli, db_cursor):
    insert_data_for_view_tests_non_published_objects(db_cursor)
    
    # Check if correct object IDs are returned in objects attributes (published objects only)
    requested_object_ids = [i for i in range(1, 11)]
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]
    body = get_objects_view_request_body(object_ids=requested_object_ids, object_data_ids=[])
    resp = await cli.post("/objects/view", json=body)
    assert resp.status == 200
    data = await resp.json()
    received_object_ids = [data["objects_attributes_and_tags"][x]["object_id"] for x in range(len(data["objects_attributes_and_tags"]))]
    ensure_equal_collection_elements(expected_object_ids, received_object_ids, 
        "Objects view, correct request as anonymous, object_ids only")    

    # Check if correct object IDs are returned in objects attributes and data (published objects only)
    # NOTE: object_data_ids only case is checked type-specific tests
    requested_object_ids = [i for i in range(1, 11)]
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]
    requested_object_data_ids = [i for i in range(3, 9)]
    expected_object_data_ids = [i for i in range(3, 9) if i % 2 == 0]
    body = get_objects_view_request_body(object_ids=requested_object_ids, object_data_ids=requested_object_data_ids)
    resp = await cli.post("/objects/view", json=body)
    assert resp.status == 200
    data = await resp.json()
    
    received_object_ids = [data["objects_attributes_and_tags"][x]["object_id"] for x in range(len(data["objects_attributes_and_tags"]))]
    ensure_equal_collection_elements(expected_object_ids, received_object_ids,
        "Objects view, correct request for both object attributes and data as anonymous, object_ids")
    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    ensure_equal_collection_elements(expected_object_data_ids, received_objects_data_ids,
        "Objects view, correct request for both object attributes and data as anonymous, object_data_ids")


async def test_view_objects_with_non_published_tags(cli, db_cursor):
    # Insert data (published objects with published & non-published tags)
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor)
    requested_object_ids = inserts["inserted_object_ids"]
    expected_object_ids = inserts["expected_object_ids_as_anonymous"]

    # Check if correct object IDs are returned in objects attributes (objects with published tags only)
    requested_object_ids = [i for i in range(1, 11)]
    body = get_objects_view_request_body(object_ids=requested_object_ids, object_data_ids=[])
    resp = await cli.post("/objects/view", json=body)
    assert resp.status == 200
    data = await resp.json()
    received_object_ids = [data["objects_attributes_and_tags"][x]["object_id"] for x in range(len(data["objects_attributes_and_tags"]))]
    ensure_equal_collection_elements(expected_object_ids, received_object_ids, 
        "Objects view, correct request as anonymous, object_ids only")
    
    # Check if correct object IDs are returned in objects attributes and data (objects with published tags only)
    # NOTE: object_data_ids only case is checked type-specific tests
    requested_object_ids = [i for i in range(1, 11)]
    expected_object_ids = [i for i in range(1, 6)]
    body = get_objects_view_request_body(object_ids=requested_object_ids, object_data_ids=requested_object_ids)
    resp = await cli.post("/objects/view", json=body)
    assert resp.status == 200
    data = await resp.json()
    received_object_ids = [data["objects_attributes_and_tags"][x]["object_id"] for x in range(len(data["objects_attributes_and_tags"]))]
    ensure_equal_collection_elements(expected_object_ids, received_object_ids,
        "Objects view, correct request for both object attributes and data as anonymous, object_ids")
    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    ensure_equal_collection_elements(expected_object_ids, received_objects_data_ids, 
        "Objects view, correct request for both object attributes and data as anonymous, object_data_ids")


if __name__ == "__main__":
    run_pytest_tests(__file__)
