import pytest

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.util import check_ids
from tests.fixtures.tags import tag_list, insert_tags
from tests.fixtures.users import headers_admin_token


async def test_incorrect_request_body_as_admin(cli):
    # Incorrect request body
    resp = await cli.post("/tags/view", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400
    
    for payload in [{}, {"tag_ids": []}, {"tag_ids": [1, -1]}, {"tag_ids": [1, "abc"]}]:
        resp = await cli.post("/tags/view", json=payload, headers=headers_admin_token)
        assert resp.status == 400


async def test_view_non_existing_tags_as_admin(cli):
    resp = await cli.post("/tags/view", json={"tag_ids": [999, 1000]}, headers=headers_admin_token)
    assert resp.status == 404


# Run the test twice for unauthorized & admin privilege levels
@pytest.mark.parametrize("headers", [None, headers_admin_token])
async def test_view_existing_tags_as_admin_and_anonymous(cli, db_cursor, config, headers):
    # Insert data
    insert_tags(tag_list, db_cursor, config)

    # Correct request
    tag_ids = [_ for _ in range(1, 11)]
    resp = await cli.post("/tags/view", json={"tag_ids": tag_ids}, headers=headers)
    assert resp.status == 200
    data = await resp.json()
    assert "tags" in data

    check_ids(tag_ids, [data["tags"][x]["tag_id"] for x in range(len(data["tags"]))], 
        "Tags view, correct request")
        
    for field in ("tag_id", "tag_name", "tag_description", "created_at", "modified_at"):
        assert field in data["tags"][0]


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
