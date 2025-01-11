if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests    

from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.data_sets.tags import incorrect_tag_values

from tests.db_operations.tags import insert_tags

from tests.request_generators.tags import get_tags_update_request_body


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.put("/tags/update", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for payload in ({}, {"test": "wrong attribute"}, {"tag": "wrong value type"}):
        resp = await cli.put("/tags/update", json=payload, headers=headers_admin_token)
        assert resp.status == 400
    
    # Missing attributes
    for attr in ("tag_id", "tag_name", "tag_description", "is_published"):
        body = get_tags_update_request_body()
        body["tag"].pop(attr)
        resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute types and lengths:
    for k, v in incorrect_tag_values:
        body = get_tags_update_request_body()
        body["tag"][k] = v
        resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_update_with_incorrect_data(cli, db_cursor):
    # Insert mock values
    tag_list = [get_test_tag(1), get_test_tag(2)]
    insert_tags(tag_list, db_cursor)
    
    # Non-existing tag_id
    body = get_tags_update_request_body(tag_id=100)
    resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
    assert resp.status == 404

    # Duplicate tag_name
    body = get_tags_update_request_body(tag_id=2)
    body["tag"]["tag_id"] = 1
    resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
    assert resp.status == 400
    
    # Lowercase duplicate tag_name
    body = get_tags_update_request_body(tag_id=2)
    body["tag"]["tag_id"] = 1
    body["tag"]["tag_name"] = body["tag"]["tag_name"].upper()
    resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_correct_update(cli, db_cursor):
    # Insert mock values
    tag_list = [get_test_tag(1)]
    insert_tags(tag_list, db_cursor)

    # Correct update
    body = get_tags_update_request_body(tag_id=3, is_published=False)
    body["tag"]["tag_id"] = 1
    resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT tag_name, tag_description, is_published FROM tags WHERE tag_id = 1")
    assert db_cursor.fetchone() == (body["tag"]["tag_name"], body["tag"]["tag_description"], body["tag"]["is_published"])


if __name__ == "__main__":
    run_pytest_tests(__file__)
