if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.data_sets.tags import incorrect_tag_attributes

from tests.db_operations.tags import insert_tags

from tests.request_generators.tags import get_tags_add_request_body


async def test_incorrect_request_body(cli):
    # Invalid JSON
    resp = await cli.post("/tags/add", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Missing top-level attributes
    resp = await cli.post("/tags/add", json={}, headers=headers_admin_token)
    assert resp.status == 400
    
    # Incorrect and unallowed top-level attributes
    incorrect_attributes = {
        "tag": [None, False, "str", 1, []],
        "unallowed": ["unallowed"]
    }
    for attr, values in incorrect_attributes.items():
        for value in values:
            body = get_tags_add_request_body()
            body[attr] = value
            resp = await cli.post("/tags/add", json=body, headers=headers_admin_token)
            assert resp.status == 400

    # Missing required tag elements
    for attr in ("tag_name", "tag_description", "is_published", "added_object_ids"):
        body = get_tags_add_request_body()
        body["tag"].pop(attr)
        resp = await cli.post("/tags/add", json=body, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect and unallowed tag attributes
    for attr, values in incorrect_tag_attributes.items():
        if attr != "tag_id":
            for value in values:
                body = get_tags_add_request_body()
                body["tag"][attr] = value
                resp = await cli.post("/tags/add", json=body, headers=headers_admin_token)
                assert resp.status == 400


async def test_add_a_duplicate_tag(cli, db_cursor):
    # Insert an existing tag
    tag_name = "tag name"
    insert_tags([get_test_tag(100, tag_name=tag_name)], db_cursor)

    # Try adding a tag with the existing name
    body = get_tags_add_request_body(tag_name=tag_name)
    resp = await cli.post("/tags/add", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Try adding a tag with the existing name in another registry
    body = get_tags_add_request_body(tag_name=tag_name.upper())
    resp = await cli.post("/tags/add", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_a_correct_tag(cli, db_cursor):
    # Write a correct tag
    body = get_tags_add_request_body(is_published=False)
    resp = await cli.post("/tags/add", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert "tag" in resp_json
    resp_tag = resp_json["tag"]
    assert type(resp_tag) == dict
    assert "tag_id" in resp_tag
    assert "created_at" in resp_tag
    assert "modified_at" in resp_tag
    assert body["tag"]["tag_name"] == resp_tag["tag_name"]
    assert body["tag"]["tag_description"] == resp_tag["tag_description"]
    assert body["tag"]["is_published"] == resp_tag["is_published"]

    db_cursor.execute("SELECT tag_name, tag_description, is_published FROM tags WHERE tag_id = 1")
    assert db_cursor.fetchone() == (body["tag"]["tag_name"], body["tag"]["tag_description"], body["tag"]["is_published"])


if __name__ == "__main__":
    run_pytest_tests(__file__)
