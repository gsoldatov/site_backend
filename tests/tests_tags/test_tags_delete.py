import json

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.fixtures.tags import get_test_tag, insert_tags
from tests.fixtures.users import headers_admin_token


async def test_incorrect_request_body_as_admin(cli):
    # Incorrect values
    for value in ["123", {"incorrect_key": "incorrect_value"}, {"tag_ids": "incorrect_value"}, {"tag_ids": []}]:
        body = value if type(value) == str else json.dumps(value)
        resp = await cli.delete("/tags/delete", data=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_delete_non_existing_tags_as_admin(cli, db_cursor, config):
    # Insert mock values
    table = config["db"]["db_schema"] + ".tags"
    tag_list = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
    insert_tags(tag_list, db_cursor, config)
    
    # Try to delete non-existing tag_id
    resp = await cli.delete("/tags/delete", json={"tag_ids": [1000, 2000]}, headers=headers_admin_token)
    assert resp.status == 404


async def test_delete_tags_as_admin(cli, db_cursor, config):
    # Insert mock values
    table = config["db"]["db_schema"] + ".tags"
    tag_list = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
    insert_tags(tag_list, db_cursor, config)

    # Correct deletes
    resp = await cli.delete("/tags/delete", json={"tag_ids": [1]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT tag_id FROM {table}")
    assert db_cursor.fetchone() == (2,)
    assert db_cursor.fetchone() == (3,)
    assert not db_cursor.fetchone()

    resp = await cli.delete("/tags/delete", json={"tag_ids": [2, 3]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT tag_id FROM {table}")
    assert not db_cursor.fetchone()


async def test_delete_tags_as_anonymous(cli, db_cursor, config):
    # Insert mock values
    table = config["db"]["db_schema"] + ".tags"
    tag_list = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
    insert_tags(tag_list, db_cursor, config)

    # Correct deletes
    resp = await cli.delete("/tags/delete", json={"tag_ids": [2, 3]})
    assert resp.status == 401
    db_cursor.execute(f"SELECT count(*) FROM {table}")
    assert db_cursor.fetchone()[0] == 3


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
