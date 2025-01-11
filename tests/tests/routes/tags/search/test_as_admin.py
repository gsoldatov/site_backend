if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.tags import get_test_tag
from tests.data_generators.sessions import headers_admin_token
from tests.data_sets.tags import tag_list
from tests.db_operations.tags import insert_tags
from tests.request_generators.tags import get_tags_search_request_body


async def test_incorrect_request_body(cli):
    # Missing and unallowed top-level attribute
    resp = await cli.post("/tags/search", json={}, headers=headers_admin_token)
    assert resp.status == 400
    
    body = get_tags_search_request_body()
    body["query"]["unallowed"] = 1
    resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
    assert resp.status == 400
    
    # Incorrect query values
    for value in ("a", 1, []):
        body = {"query": value}
        resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Missing query attributes
    for attr in ("query_text", "maximum_values", "existing_ids"):
        body = get_tags_search_request_body()
        body["query"].pop(attr)
        resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed query attribute
    body = get_tags_search_request_body()
    body["unallowed"] = 1
    resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
    assert resp.status == 400
    
    # Incorrect query attribute values
    incorrect_attributes = {
        "query_text": [1, False, [], {}, "", "a" * 256],
        "maximum_values": ["a", [], {}, -1, 0, 101],
        "existings_ids": [1, False, "a", {}, ["a"], [-1], [0], [1] * 1001]
    }
    for attr, values in incorrect_attributes.items():
        for value in values:
            body = get_tags_search_request_body()
            body["query"][attr] = value
            resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
            assert resp.status == 400


async def test_search_non_existing_tags(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)
    
    body = get_tags_search_request_body(query_text="non-existing tag")
    resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
    assert resp.status == 404


async def test_correct_requests(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)

    # Correct request - check response and maximum_values limit
    body = get_tags_search_request_body(query_text="0", maximum_values=2)
    resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "tag_ids" in data
    assert type(data["tag_ids"]) == list
    assert data["tag_ids"] == [1, 3]    # a0, c0

    # Correct request - check if query_text case is ignored
    insert_tags([get_test_tag(11, created_at=tag_list[0]["created_at"], modified_at=tag_list[0]["modified_at"], 
                    tag_name="A", tag_description="")]
                    , db_cursor)
    body = get_tags_search_request_body(query_text="A")
    resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [1, 11]    #a0, A

    body = get_tags_search_request_body(query_text="a")
    resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [1, 11]    #a0, A

    # Correct request - check if existing_ids are excluded from result
    body = get_tags_search_request_body(query_text="0", maximum_values=2, existing_ids=[1, 3, 9])
    resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [5, 7]    #e0, g0


async def test_correct_request_published_tags(cli, db_cursor):
    # Insert data
    insert_tags([
        get_test_tag(1, tag_name="a1", is_published=False),
        get_test_tag(2, tag_name="a2", is_published=True),
        get_test_tag(3, tag_name="a3", is_published=False),
        get_test_tag(4, tag_name="a4", is_published=True),
        get_test_tag(7, tag_name="b1", is_published=True),
        get_test_tag(8, tag_name="b2", is_published=False)
    ], db_cursor)

    # Check if tags are returned regardless of their `is_published` prop
    body = get_tags_search_request_body(query_text="a", maximum_values=2)
    resp = await cli.post("/tags/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "tag_ids" in data
    assert type(data["tag_ids"]) == list
    assert data["tag_ids"] == [1, 2]    # a1, a2


if __name__ == "__main__":
    run_pytest_tests(__file__)
