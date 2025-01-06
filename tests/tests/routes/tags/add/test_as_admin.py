if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.data_sets.tags import incorrect_tag_values

from tests.db_operations.tags import insert_tags


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.post("/tags/add", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Check required elements
    for attr in ("tag_name", "tag_description", "is_published"):
        tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
        tag.pop(attr)
        resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 400

    # Unallowed elements
    tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
    tag["unallowed"] = "unallowed"
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    for k, v in incorrect_tag_values:
        if k != "tag_id":
            tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
            tag[k] = v
            resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
            assert resp.status == 400


async def test_add_a_duplicate_tag(cli, db_cursor):
    # Insert an existing tag
    tag_name = "tag name"
    insert_tags([get_test_tag(100, tag_name=tag_name)], db_cursor)

    # Try adding a tag with the existing name
    tag = get_test_tag(1, tag_name=tag_name, pop_keys=["tag_id", "created_at", "modified_at"])
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400

    # Try adding a tag with the existing name in another registry
    tag = get_test_tag(1, tag_name=tag_name.upper(), pop_keys=["tag_id", "created_at", "modified_at"])
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_a_correct_tag(cli, db_cursor):
    # Write a correct tag
    tag_id = 1
    tag = get_test_tag(tag_id, is_published=False, pop_keys=["tag_id", "created_at", "modified_at"])
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert "tag" in resp_json
    resp_tag = resp_json["tag"]
    assert type(resp_tag) == dict
    assert "tag_id" in resp_tag
    assert "created_at" in resp_tag
    assert "modified_at" in resp_tag
    assert tag["tag_name"] == resp_tag["tag_name"]
    assert tag["tag_description"] == resp_tag["tag_description"]
    assert tag["is_published"] == resp_tag["is_published"]

    db_cursor.execute(f"SELECT tag_name, tag_description, is_published FROM tags WHERE tag_id = {tag_id}")
    assert db_cursor.fetchone() == (tag["tag_name"], tag["tag_description"], tag["is_published"])


if __name__ == "__main__":
    run_pytest_tests(__file__)
