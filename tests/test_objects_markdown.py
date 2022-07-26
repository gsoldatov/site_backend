"""
Tests for markdown-specific operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))
    from tests.util import run_pytest_tests

from util import check_ids
from fixtures.objects import get_test_object, get_objects_attributes_list, get_test_object_data, \
    markdown_data_list, insert_objects, insert_markdown, insert_data_for_view_tests_objects_with_non_published_tags
from tests.fixtures.sessions import headers_admin_token


async def test_add(cli, db_cursor):
    # Incorrect markdown attributes
    for attr in [{"incorrect MD attr": "123"}, {"incorrect MD attr": "123", "raw_text": "New text"}]:
        md = get_test_object(4, pop_keys=["object_id", "created_at", "modified_at"])
        md["object_data"] = attr
        resp = await cli.post("/objects/add", json={"object": md}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect markdown value
    md = get_test_object(4, pop_keys=["object_id", "created_at", "modified_at"])
    md["object_data"] = {"raw_text": ""}
    resp = await cli.post("/objects/add", json={"object": md}, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute(f"SELECT object_name FROM objects") # Check that a new object was not created
    assert not db_cursor.fetchone()
    db_cursor.execute(f"SELECT raw_text FROM markdown")
    assert not db_cursor.fetchone()

    # Add a correct markdown object
    md = get_test_object(4, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": md}, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert "object" in resp_json
    resp_object = resp_json["object"]

    db_cursor.execute(f"SELECT raw_text FROM markdown WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (md["object_data"]["raw_text"],)


async def test_update(cli, db_cursor):
    # Insert mock values
    obj_list = [get_test_object(4, owner_id=1, pop_keys=["object_data"]), get_test_object(5, owner_id=1, pop_keys=["object_data"])]
    md_list = [get_test_object_data(4), get_test_object_data(5)]
    insert_objects(obj_list, db_cursor)
    insert_markdown(md_list, db_cursor)

    # Incorrect attributes in object_data for markdown
    for object_data in [{}, {"raw_text": "Some text", "incorrect_attr": 1}, {"raw_text": ""}, {"raw_text": 123}]:
        obj = get_test_object(6, pop_keys=["created_at", "modified_at", "object_type"])
        obj["object_id"] = 4
        obj["object_data"] = object_data
        resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 400

    # Correct update (markdown)
    obj = get_test_object(6, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 4
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT raw_text FROM markdown WHERE object_id = 4")
    assert db_cursor.fetchone() == (obj["object_data"]["raw_text"],)


async def test_view_non_published_objects(cli, db_cursor):
    # Insert mock values
    insert_objects(get_objects_attributes_list(11, 20), db_cursor)
    insert_markdown(markdown_data_list, db_cursor)

    # Correct request (object_data_ids only, markdown), non-existing ids
    object_data_ids = [_ for _ in range(1001, 1011)]
    resp = await cli.post("/objects/view", json={"object_data_ids": object_data_ids}, headers=headers_admin_token)
    assert resp.status == 404
    
    # Correct request (object_data_ids only, markdown)
    object_data_ids = [_ for _ in range(11, 21)]
    resp = await cli.post("/objects/view", json={"object_data_ids": object_data_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "object_data" in data

    for field in ("object_id", "object_type", "object_data"):
        assert field in data["object_data"][0]
    assert "raw_text" in data["object_data"][0]["object_data"]

    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as admin, markdown object_data_ids only")


async def test_view_objects_with_non_published_tags(cli, db_cursor):
    # Insert data (published objects with published & non-published tags)
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor, object_type="markdown")
    requested_object_ids = inserts["inserted_object_ids"]

    # Correct request (object_ids only)
    resp = await cli.post("/objects/view", json={"object_data_ids": requested_object_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    check_ids(requested_object_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as admin, markdown object_data_ids only")


async def test_delete(cli, db_cursor):
    # Insert mock values
    obj_list = [get_test_object(4, owner_id=1, pop_keys=["object_data"]), 
        get_test_object(5, owner_id=1, pop_keys=["object_data"]), get_test_object(6, owner_id=1, pop_keys=["object_data"])]
    md_list = [get_test_object_data(4), get_test_object_data(5), get_test_object_data(6)]
    insert_objects(obj_list, db_cursor)
    insert_markdown(md_list, db_cursor)

    # Correct deletes (general data + markdown)
    resp = await cli.delete("/objects/delete", json={"object_ids": [4]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM markdown")
    assert db_cursor.fetchone() == (5,)
    assert db_cursor.fetchone() == (6,)
    assert not db_cursor.fetchone()

    resp = await cli.delete("/objects/delete", json={"object_ids": [5, 6]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM markdown")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
