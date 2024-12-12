if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests    

from tests.fixtures.data_generators.objects import get_objects_attributes_list
from tests.fixtures.data_generators.sessions import headers_admin_token
from tests.fixtures.data_generators.tags import get_test_tag

from tests.fixtures.data_sets.tags import incorrect_tag_values

from tests.fixtures.db_operations.objects import insert_objects
from tests.fixtures.db_operations.objects_tags import insert_objects_tags
from tests.fixtures.db_operations.tags import insert_tags


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.put("/tags/update", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for payload in ({}, {"test": "wrong attribute"}, {"tag": "wrong value type"}):
        resp = await cli.put("/tags/update", json=payload, headers=headers_admin_token)
        assert resp.status == 400
    
    # Missing attributes
    for attr in ("tag_id", "tag_name", "tag_description", "is_published"):
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


async def test_update_with_incorrect_data(cli, db_cursor):
    # Insert mock values
    tag_list = [get_test_tag(1), get_test_tag(2)]
    insert_tags(tag_list, db_cursor)
    
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


async def test_correct_update(cli, db_cursor):
    # Insert mock values
    tag_list = [get_test_tag(1)]
    insert_tags(tag_list, db_cursor)

    # Correct update
    tag = get_test_tag(3, is_published=False, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 1
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT tag_name, tag_description, is_published FROM tags WHERE tag_id = 1")
    assert db_cursor.fetchone() == (tag["tag_name"], tag["tag_description"], tag["is_published"])


async def test_update_tag_with_added_and_removed_object_ids(cli, db_cursor):
    # Insert mock data
    insert_objects(get_objects_attributes_list(1, 10), db_cursor)
    insert_tags([get_test_tag(1)], db_cursor)
    insert_objects_tags([1, 2, 3, 4, 5], [1], db_cursor)

    # Incorrect added_object_ids and removed_object_ids
    for added_object_ids in ["not a list", 1, {}]:
        tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
        tag["added_object_ids"] = added_object_ids
        resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 400
    
    for removed_object_ids in ["not a list", 1, {}]:
        tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
        tag["removed_object_ids"] = removed_object_ids
        resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Attempt to tag non-existing objects (and get a 404 error)
    tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
    tag["added_object_ids"] = [1, 100]
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400

    # Tag/untag existing objects (and check duplicate object_ids handling)
    tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
    tag["added_object_ids"] = [3, 4, 6, 7, 6, 7]
    tag["removed_object_ids"] = [1, 2]
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_object_ids = data.get("tag", {}).get("object_updates", {}).get("added_object_ids")
    assert sorted(added_object_ids) == [3, 4, 6, 7]
    db_cursor.execute(f"SELECT object_id FROM objects_tags WHERE tag_id = {data['tag']['tag_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [3, 4, 5, 6, 7] # 1, 2 were removed; 6, 7 were added

    # Tag objects only
    tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
    tag["added_object_ids"] = [1, 2, 3, 1, 2]
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    added_object_ids = data.get("tag", {}).get("object_updates", {}).get("added_object_ids")
    assert sorted(added_object_ids) == [1, 2, 3]
    db_cursor.execute(f"SELECT object_id FROM objects_tags WHERE tag_id = {data['tag']['tag_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 6, 7] # 1, 2 were added

    # Untag objects only
    tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
    tag["removed_object_ids"] = [2, 1, 1, 2]
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    removed_object_ids = data.get("tag", {}).get("object_updates", {}).get("removed_object_ids")
    assert sorted(removed_object_ids) == [1, 2]
    db_cursor.execute(f"SELECT object_id FROM objects_tags WHERE tag_id = {data['tag']['tag_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [3, 4, 5, 6, 7] # 1, 2 were removed


if __name__ == "__main__":
    run_pytest_tests(__file__)
