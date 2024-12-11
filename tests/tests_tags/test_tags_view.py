if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.util import check_ids
from tests.fixtures.data_sets.tags import tag_list
from tests.fixtures.db_operations.tags import insert_tags

from tests.fixtures.data_generators.sessions import headers_admin_token


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.post("/tags/view", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400
    
    for payload in [{}, {"tag_ids": []}, {"tag_ids": [1, -1]}, {"tag_ids": [1, "abc"]}]:
        resp = await cli.post("/tags/view", json=payload, headers=headers_admin_token)
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
    check_ids(tag_ids, [data["tags"][x]["tag_id"] for x in range(len(data["tags"]))], 
        "Tags view, correct request")
        
    for field in ("tag_id", "tag_name", "tag_description", "created_at", "modified_at", "tag_description"):
        assert field in data["tags"][0]


if __name__ == "__main__":
    run_pytest_tests(__file__)
