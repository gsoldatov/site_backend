if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_objects_attributes_list, get_object_attrs
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.objects import insert_data_for_view_tests_objects_with_non_published_tags

from tests.db_operations.objects import insert_objects

from tests.request_generators.objects import get_objects_search_request_body


async def test_incorrect_request_body(cli):
    # Invalid JSON
    resp = await cli.post("/objects/search", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Missing, incorrect and unallowed top-level attributes
    for body in ("a", {}, {**get_objects_search_request_body(), "unallowed": 1}):
        resp = await cli.post("/objects/search", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Missing query attributes
    for attr in ("query_text", "maximum_values", "existing_ids"):
        body = get_objects_search_request_body()
        body["query"].pop(attr)
        resp = await cli.post("/objects/search", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed query attribute
    body = get_objects_search_request_body()
    body["query"]["unallowed"] = 1
    resp = await cli.post("/objects/search", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect query attribute values
    incorrect_values = {
        "query_text": [None, 1, False, {}, [], "", "a" * 256],
        "maximum_values": [None, False, "a", {}, [], -1, 0],
        "existing_ids": [None, 1, False, "a", {}, ["a"], [-1], [0], [1] * 101]
    }
    for attr, values in incorrect_values.items():
        for value in values:
            body = get_objects_search_request_body()
            body["query"][attr] = value
            resp = await cli.post("/objects/search", json=body, headers=headers_admin_token)
            assert resp.status == 400


async def test_search_non_existing_objects(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)
    insert_objects(obj_list, db_cursor)

    body = get_objects_search_request_body(query_text="non-existing object")
    resp = await cli.post("/objects/search", json=body, headers=headers_admin_token)
    assert resp.status == 404


async def test_correct_search_non_published_objects(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)
    insert_objects(obj_list, db_cursor)

    # Correct request - check response and maximum_values limit
    body = get_objects_search_request_body(query_text="0", maximum_values=2)
    resp = await cli.post("/objects/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "object_ids" in data
    assert type(data["object_ids"]) == list
    assert data["object_ids"] == [1, 3]    # a0, c0

    # Correct request - check if query case is ignored
    insert_objects([get_object_attrs(
        object_id=11, object_type="link", created_at=obj_list[0]["created_at"], modified_at=obj_list[0]["modified_at"],
        object_name="A", object_description="", is_published=False, show_description=True
    )], db_cursor)
    body = get_objects_search_request_body(query_text="A")
    resp = await cli.post("/objects/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["object_ids"] == [1, 11]    #a0, A

    body = get_objects_search_request_body(query_text="a")
    resp = await cli.post("/objects/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["object_ids"] == [1, 11]    #a0, A

    # Correct request - check if existing_ids are excluded from result
    body = get_objects_search_request_body(query_text="0", maximum_values=2, existing_ids=[1, 3, 9])
    resp = await cli.post("/objects/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["object_ids"] == [5, 7]    #e0, g0


async def test_correct_search_objects_with_non_published_tags(cli, db_cursor):
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor)
    expected_object_ids = inserts["inserted_object_ids"]

    # Search a pattern matching all existing objects (and receive all objects, 
    # regardless of being tagged with non-published tags, in the response)
    body = get_objects_search_request_body()
    resp = await cli.post("/objects/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert sorted(data["object_ids"]) == expected_object_ids


if __name__ == "__main__":
    run_pytest_tests(__file__)
