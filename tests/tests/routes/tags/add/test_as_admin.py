if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_objects_attributes_list

from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.data_sets.tags import incorrect_tag_values

from tests.db_operations.objects import insert_objects, insert_links


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


async def test_add_tag_with_added_object_ids(cli, db_cursor):
    # Insert mock data
    insert_objects(get_objects_attributes_list(1, 10), db_cursor)
    
    # Incorrect tag's objects
    for added_object_ids in ["not a list", 1, {}]:
        tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
        tag["added_object_ids"] = added_object_ids
        resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 400

    # Attempt to tag non-existing objects
    tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
    tag["added_object_ids"] = [1, 100]
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400

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
