if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests    

from tests.data_generators.objects import get_object_attrs, get_objects_attributes_list
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags

from tests.request_generators.tags import get_tags_update_request_body


async def test_incorrect_request_body(cli, db_cursor):
    insert_tags([get_test_tag(1)], db_cursor)
    insert_objects([get_object_attrs(1)], db_cursor)

    # Incorrect types
    for added_object_ids in [None, False, "not a list", 1, {}, ["a"], [-1], [0]]:
        body = get_tags_update_request_body()
        body["tag"]["added_object_ids"] = added_object_ids
        resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Too many added objects
    body = get_tags_update_request_body(added_object_ids=[1] * 101)
    resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_non_existing_object_ids(cli, db_cursor):
    # Insert an existing object
    insert_tags([get_test_tag(1, tag_name="old name")], db_cursor)
    insert_objects([get_object_attrs(1)], db_cursor)

    # Try adding a tag with non-existing object IDs
    body = get_tags_update_request_body(tag_name="new name", added_object_ids=[1, 2, 3])
    resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute(f"SELECT tag_name FROM tags WHERE tag_id = 1")
    assert db_cursor.fetchone()[0] == "old name"


async def test_update_tag_with_empty_added_object_ids(cli, db_cursor):
    # Insert existing data
    insert_tags([get_test_tag(1, tag_name="old name")], db_cursor)
    insert_objects([get_object_attrs(1)], db_cursor)
    insert_objects_tags([1], [1], db_cursor)

    # Update tag & check if tag was updated, but objects_tags were not
    body = get_tags_update_request_body(tag_name="new name", added_object_ids=[])
    resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
    assert resp.status == 200

    db_cursor.execute(f"SELECT tag_name FROM tags WHERE tag_id = 1")
    assert db_cursor.fetchone()[0] == "new name"

    db_cursor.execute(f"SELECT object_id FROM objects_tags WHERE tag_id = 1")
    assert [r[0] for r in db_cursor.fetchall()] == [1]


async def test_correctly_update_a_tag(cli, db_cursor):
    # Insert mock data
    insert_objects(get_objects_attributes_list(1, 5), db_cursor)
    insert_tags([get_test_tag(1, tag_name="old name")], db_cursor)
    insert_objects_tags([1, 2], [1], db_cursor)

    # Update tag and check duplicate & already tagged object_ids handling
    body = get_tags_update_request_body(tag_name="new name", added_object_ids=[2, 3, 4, 5, 4, 5])
    resp = await cli.put("/tags/update", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_object_ids = data["tag"]["added_object_ids"]
    assert sorted(added_object_ids) == [2, 3, 4, 5]
    db_cursor.execute(f"SELECT object_id FROM objects_tags WHERE tag_id = {data['tag']['tag_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5]


if __name__ == "__main__":
    run_pytest_tests(__file__)
