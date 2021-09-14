import pytest

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.fixtures.tags import tag_list, insert_tags
from tests.fixtures.users import headers_admin_token


async def test_incorrect_request_body_as_admin(cli):
    # Incorrect request
    for req_body in ["not an object", 1, {"incorrect attribute": {}}, {"query": "not an object"}, {"query": 1},
        {"query": {"query_text": "123"}, "incorrect attribute": {}}, {"query": {"incorrect attribute": "123"}},
        {"query": {"query_text": "123", "incorrect_attribute": 1}}]:
        resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute values
    for req_body in [{"query": {"query_text": ""}}, {"query": {"query_text": 1}}, {"query": {"query_text": "a"*256}},
        {"query": {"query_text": "123", "maximum_values": "1"}}, {"query": {"query_text": "123", "maximum_values": -1}},
        {"query": {"query_text": "123", "maximum_values": 101}}]:
        resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
        assert resp.status == 400


async def test_search_non_existing_tags_as_admin(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)
    
    req_body = {"query": {"query_text": "non-existing tag"}}
    resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 404


# Run the test twice for unauthorized & admin privilege levels
@pytest.mark.parametrize("headers", [None, headers_admin_token])
async def test_correct_search_requests_as_admin_and_anonymous(cli, db_cursor, headers):
    # Insert data
    insert_tags(tag_list, db_cursor)

    # Correct request - check response and maximum_values limit
    req_body = {"query": {"query_text": "0", "maximum_values": 2}}
    resp = await cli.post("/tags/search", json=req_body, headers=headers)
    assert resp.status == 200
    data = await resp.json()
    assert "tag_ids" in data
    assert type(data["tag_ids"]) == list
    assert data["tag_ids"] == [1, 3]    # a0, c0

    # Correct request - check if query case is ignored
    insert_tags([{"tag_id": 11, "created_at": tag_list[0]["created_at"], "modified_at": tag_list[0]["modified_at"], 
                    "tag_name": "A", "tag_description": ""}]
                    , db_cursor)
    req_body = {"query": {"query_text": "A"}}
    resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [1, 11]    #a0, A

    req_body = {"query": {"query_text": "a"}}
    resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [1, 11]    #a0, A

    # Correct request - check if existing_ids are excluded from result
    req_body = {"query": {"query_text": "0", "maximum_values": 2, "existing_ids": [1, 3, 9]}}
    resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [5, 7]    #e0, g0


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
