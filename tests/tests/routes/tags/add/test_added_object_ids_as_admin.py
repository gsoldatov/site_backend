if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_objects_attributes_list

from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.db_operations.objects import insert_objects


async def test_incorrect_request_body(cli, db_cursor):
    # Incorrect tag's objects
    for added_object_ids in ["not a list", 1, {}, [-1], [0]]:
        tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
        tag["added_object_ids"] = added_object_ids
        resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Too many added objects
    tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
    tag["added_object_ids"] = ["a"] * 101
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_non_existing_object_ids(cli, db_cursor):
    # Insert an existing object
    insert_objects([get_test_object(1, owner_id=1, pop_keys=["object_data"])], db_cursor)

    # Try adding a tag with non-existing object IDs
    tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
    tag["added_object_ids"] = [1, 2, 3]

    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute(f"SELECT tag_id FROM tags WHERE tag_id = 1")
    assert not db_cursor.fetchone()


async def test_add_a_correct_tag_with_empty_added_object_ids(cli, db_cursor):
    tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
    tag["added_object_ids"] = []
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 200

    db_cursor.execute(f"SELECT tag_id FROM tags WHERE tag_id = 1")
    assert db_cursor.fetchone()

    db_cursor.execute(f"SELECT object_id FROM objects_tags WHERE tag_id = 1")
    assert not db_cursor.fetchone()


async def test_add_correct_tag(cli, db_cursor):
    # Insert mock data
    insert_objects(get_objects_attributes_list(1, 10), db_cursor)

    # Tag existing objects (and check duplicate object_ids handling)
    tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
    tag["added_object_ids"] = [1, 2, 4, 6, 4, 6, 4, 6]
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_object_ids = data.get("tag", {}).get("object_updates", {}).get("added_object_ids")
    assert sorted(added_object_ids) == [1, 2, 4, 6]
    db_cursor.execute(f"SELECT object_id FROM objects_tags WHERE tag_id = {data['tag']['tag_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 4, 6]


if __name__ == "__main__":
    run_pytest_tests(__file__)
