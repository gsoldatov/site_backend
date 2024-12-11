if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.tags import get_test_tag, incorrect_tag_values
from tests.fixtures.data_generators.sessions import headers_admin_token


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


async def test_add_a_correct_tag_and_a_duplicate(cli, db_cursor):
    # Write a correct tag
    tag = get_test_tag(1, is_published=False, pop_keys=["tag_id", "created_at", "modified_at"])
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

    db_cursor.execute(f"SELECT tag_name, tag_description, is_published FROM tags WHERE tag_id = 1")
    assert db_cursor.fetchone() == (tag["tag_name"], tag["tag_description"], tag["is_published"])

    # Add an existing tag_name
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400


if __name__ == "__main__":
    run_pytest_tests(__file__)
