import json

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.tags import get_test_tag, insert_tags
from tests.fixtures.sessions import headers_admin_token


async def test_incorrect_request_body(cli):
    # Incorrect values
    for value in ["123", {"incorrect_key": "incorrect_value"}, {"tag_ids": "incorrect_value"}, {"tag_ids": []}]:
        body = value if type(value) == str else json.dumps(value)
        resp = await cli.delete("/tags/delete", data=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_delete_non_existing_tags(cli, db_cursor):
    # Insert mock values
    tag_list = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
    insert_tags(tag_list, db_cursor)
    
    # Try to delete non-existing tag_id
    resp = await cli.delete("/tags/delete", json={"tag_ids": [1000, 2000]}, headers=headers_admin_token)
    assert resp.status == 404


async def test_delete_tags(cli, db_cursor):
    # Insert mock values
    tag_list = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
    insert_tags(tag_list, db_cursor)

    # Correct deletes
    resp = await cli.delete("/tags/delete", json={"tag_ids": [1]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT tag_id FROM tags")
    assert db_cursor.fetchone() == (2,)
    assert db_cursor.fetchone() == (3,)
    assert not db_cursor.fetchone()

    resp = await cli.delete("/tags/delete", json={"tag_ids": [2, 3]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT tag_id FROM tags")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
