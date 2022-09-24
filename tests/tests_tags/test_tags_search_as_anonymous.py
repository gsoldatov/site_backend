if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.tags import tag_list, insert_tags, get_test_tag


async def test_correct_search_requests(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)

    # Correct request - check response and maximum_values limit
    req_body = {"query": {"query_text": "0", "maximum_values": 2}}
    resp = await cli.post("/tags/search", json=req_body)
    assert resp.status == 200
    data = await resp.json()
    assert "tag_ids" in data
    assert type(data["tag_ids"]) == list
    assert data["tag_ids"] == [1, 3]    # a0, c0

    # Correct request - check if query case is ignored
    insert_tags([get_test_tag(11, created_at=tag_list[0]["created_at"], modified_at=tag_list[0]["modified_at"], 
                    tag_name="A", tag_description="")]
                    , db_cursor)
    req_body = {"query": {"query_text": "A"}}
    resp = await cli.post("/tags/search", json=req_body)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [1, 11]    #a0, A

    req_body = {"query": {"query_text": "a"}}
    resp = await cli.post("/tags/search", json=req_body)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [1, 11]    #a0, A

    # Correct request - check if existing_ids are excluded from result
    req_body = {"query": {"query_text": "0", "maximum_values": 2, "existing_ids": [1, 3, 9]}}
    resp = await cli.post("/tags/search", json=req_body)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [5, 7]    #e0, g0


if __name__ == "__main__":
    run_pytest_tests(__file__)
