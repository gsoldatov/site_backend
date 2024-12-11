if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.objects import get_objects_attributes_list, get_test_object
from tests.fixtures.data_generators.sessions import headers_admin_token

from tests.fixtures.data_sets.objects import insert_data_for_view_tests_objects_with_non_published_tags

from tests.fixtures.db_operations.objects import insert_objects


async def test_incorrect_request_body(cli):
    # Incorrect request
    for req_body in ["not an object", 1, {"incorrect attribute": {}}, {"query": "not an object"}, {"query": 1},
        {"query": {"query_text": "123"}, "incorrect attribute": {}}, {"query": {"incorrect attribute": "123"}},
        {"query": {"query_text": "123", "incorrect_attribute": 1}}]:
        resp = await cli.post("/objects/search", json=req_body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute values
    for req_body in [{"query": {"query_text": ""}}, {"query": {"query_text": 1}}, {"query": {"query_text": "a"*256}},
        {"query": {"query_text": "123", "maximum_values": "1"}}, {"query": {"query_text": "123", "maximum_values": -1}},
        {"query": {"query_text": "123", "maximum_values": 101}}]:
        resp = await cli.post("/objects/search", json=req_body, headers=headers_admin_token)
        assert resp.status == 400


async def test_search_non_existing_objects(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)
    insert_objects(obj_list, db_cursor)

    req_body = {"query": {"query_text": "non-existing object"}}
    resp = await cli.post("/objects/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 404


async def test_correct_search_non_published_objects(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)
    insert_objects(obj_list, db_cursor)

    # Correct request - check response and maximum_values limit
    req_body = {"query": {"query_text": "0", "maximum_values": 2}}
    resp = await cli.post("/objects/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "object_ids" in data
    assert type(data["object_ids"]) == list
    assert data["object_ids"] == [1, 3]    # a0, c0

    # Correct request - check if query case is ignored
    insert_objects([get_test_object(object_id=11, object_type="link", created_at=obj_list[0]["created_at"], modified_at=obj_list[0]["modified_at"], 
                    object_name="A", object_description="", is_published=False, show_description=True, owner_id=1)]
                , db_cursor)
    req_body = {"query": {"query_text": "A"}}
    resp = await cli.post("/objects/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["object_ids"] == [1, 11]    #a0, A

    req_body = {"query": {"query_text": "a"}}
    resp = await cli.post("/objects/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["object_ids"] == [1, 11]    #a0, A

    # Correct request - check if existing_ids are excluded from result
    req_body = {"query": {"query_text": "0", "maximum_values": 2, "existing_ids": [1, 3, 9]}}
    resp = await cli.post("/objects/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["object_ids"] == [5, 7]    #e0, g0


async def test_correct_search_objects_with_non_published_tags(cli, db_cursor):
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor)
    expected_object_ids = inserts["inserted_object_ids"]

    # Search a pattern matching all existing objects (and receive all objects, 
    # regardless of being tagged with non-published tags, in the response)
    req_body = {"query": {"query_text": "object", "maximum_values": 10}}
    resp = await cli.post("/objects/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert sorted(data["object_ids"]) == expected_object_ids


if __name__ == "__main__":
    run_pytest_tests(__file__)
