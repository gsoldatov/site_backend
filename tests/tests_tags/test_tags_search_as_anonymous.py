if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.tags import insert_tags, get_test_tag


async def test_correct_request(cli, db_cursor):
    # Insert data
    insert_tags([
        get_test_tag(1, tag_name="a1", is_published=True),
        get_test_tag(2, tag_name="a2", is_published=False),
        get_test_tag(3, tag_name="a3", is_published=False),
        get_test_tag(4, tag_name="a4", is_published=True),
        get_test_tag(5, tag_name="a5", is_published=True),
        get_test_tag(6, tag_name="a6", is_published=True),
        get_test_tag(7, tag_name="b1", is_published=True),
        get_test_tag(8, tag_name="b2", is_published=False)
    ], db_cursor)

    # Check if only published tags are returned
    req_body = {"query": {"query_text": "a", "maximum_values": 2}}
    resp = await cli.post("/tags/search", json=req_body)
    assert resp.status == 200
    data = await resp.json()
    assert "tag_ids" in data
    assert type(data["tag_ids"]) == list
    assert data["tag_ids"] == [1, 4]    # a1, a4 (a2 & a3 are not published, a5 & a6 are not returned due to `maximum_values` param


if __name__ == "__main__":
    run_pytest_tests(__file__)
