import json

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_objects_attributes_list
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags


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


async def test_objects_tags_deletion(cli, db_cursor):
    # Insert mock values
    insert_objects(get_objects_attributes_list(1, 10), db_cursor)
    tags = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
    insert_tags(tags, db_cursor)
    tags_objects = {1: [1, 2, 3], 2: [3, 4, 5], 3: [1, 2, 3, 4, 5]}
    insert_objects_tags(tags_objects[1], [1], db_cursor)
    insert_objects_tags(tags_objects[2], [2], db_cursor)
    insert_objects_tags(tags_objects[3], [3], db_cursor)

    # Delete 2 tags
    resp = await cli.delete("/tags/delete", json={"tag_ids": [1, 2]}, headers=headers_admin_token)
    assert resp.status == 200

    for id in [1, 2]:
        db_cursor.execute(f"SELECT * FROM objects_tags WHERE tag_id = {id}")
        assert not db_cursor.fetchone()
    db_cursor.execute(f"SELECT object_id FROM objects_tags WHERE tag_id = 3")
    assert sorted(tags_objects[3]) == sorted([r[0] for r in db_cursor.fetchall()])

if __name__ == "__main__":
    run_pytest_tests(__file__)
