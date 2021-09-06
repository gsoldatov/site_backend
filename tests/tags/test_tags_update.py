import os
import pytest

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.fixtures.tags import get_test_tag, incorrect_tag_values, insert_tags
from tests.fixtures.users import headers_admin_token


async def test_incorrect_request_body_as_admin(cli):
    # Incorrect request body
    resp = await cli.put("/tags/update", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for payload in ({}, {"test": "wrong attribute"}, {"tag": "wrong value type"}):
        resp = await cli.put("/tags/update", json=payload, headers=headers_admin_token)
        assert resp.status == 400
    
    # Missing attributes
    for attr in ("tag_id", "tag_name", "tag_description"):
        tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
        tag.pop(attr)
        resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute types and lengths:
    for k, v in incorrect_tag_values:
        tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
        tag[k] = v
        resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 400


async def test_update_with_incorrect_data_as_admin(cli, db_cursor, config):
    # Insert mock values
    table = config["db"]["db_schema"] + ".tags"
    tag_list = [get_test_tag(1), get_test_tag(2)]
    insert_tags(tag_list, db_cursor, config)
    
    # Non-existing tag_id
    tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 100
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 404

    # Duplicate tag_name
    tag = get_test_tag(2, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 1
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400
    
    # Lowercase duplicate tag_name
    tag = get_test_tag(2, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 1
    tag["tag_name"] = tag["tag_name"].upper()
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400


async def test_correct_update_as_admin(cli, db_cursor, config):
    # Insert mock values
    table = config["db"]["db_schema"] + ".tags"
    tag_list = [get_test_tag(1)]
    insert_tags(tag_list, db_cursor, config)

    # Correct update
    tag = get_test_tag(3, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 1
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT tag_name FROM {table} WHERE tag_id = 1")
    assert db_cursor.fetchone() == (tag["tag_name"],)


async def test_correct_update_as_anonymous(cli, db_cursor, config):
    # Insert mock values
    table = config["db"]["db_schema"] + ".tags"
    tag_list = [get_test_tag(1)]
    insert_tags(tag_list, db_cursor, config)

    tag = get_test_tag(3, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 1
    resp = await cli.put("/tags/update", json={"tag": tag})
    assert resp.status == 401
    db_cursor.execute(f"SELECT tag_name FROM {table} WHERE tag_id = 1")
    assert db_cursor.fetchone() == (tag_list[0]["tag_name"],)


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
