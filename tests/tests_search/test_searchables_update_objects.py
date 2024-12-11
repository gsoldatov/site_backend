"""
Tests for automatic object processing after route handler execution.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests    

from datetime import datetime

from tests.fixtures.objects import get_test_object, get_test_object_data, insert_objects, insert_links
from tests.fixtures.data_generators.searchables import get_test_searchable
from tests.fixtures.db_operations.searchables import insert_searchables
from tests.fixtures.sessions import headers_admin_token

from tests.util import wait_for


async def test_add_objects_attribute_search(cli_with_search, db_cursor):
    # Add 2 objects
    for w in ("first", "second"):
        object_name = f"{w} name"
        object_description = f"{w} descr"
        obj = get_test_object(1, object_name=object_name, object_description=object_description, pop_keys=["object_id", "created_at", "modified_at"])
        resp = await cli_with_search.post("/objects/add", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables")
        return db_cursor.fetchone()[0] == 2

    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if tags can are found by their names and descriptions
    for f in ("name", "descr"):
        for i, w in enumerate(("first", "second")):
            object_id = i + 1
            query_text = f"{w} {f}"
            body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
            resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
            assert resp.status == 200
            resp_json = await resp.json()
            assert resp_json["items"] == [{"item_id": object_id, "item_type": "object"}]


async def test_update_objects_attribute_search(cli_with_search, db_cursor):
    # Insert mock values
    obj_list = [get_test_object(1, owner_id=1, pop_keys=["object_data"]), get_test_object(2, owner_id=1, pop_keys=["object_data"])]
    insert_objects(obj_list, db_cursor)
    old_modified_at = datetime(2001, 1, 1)
    insert_links([get_test_object_data(1), get_test_object_data(2)], db_cursor)
    searchables = [get_test_searchable(object_id=i+1, text_a=f"old {w}", modified_at=old_modified_at) for i,w in enumerate(("first", "second"))]
    insert_searchables(searchables, db_cursor)

    # Update both objects
    for i, w in enumerate(("first", "second")):
        obj = get_test_object(i + 1, object_name=f"updated {w} name", object_description=f"updated {w} descr", pop_keys=["object_type", "created_at", "modified_at"])
        resp = await cli_with_search.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 200

    # Wait for object searchables to be updated
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables WHERE modified_at > %(old_modified_at)s", {"old_modified_at": old_modified_at})
        return db_cursor.fetchone()[0] == 2

    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if old searchables are no longer present
    for i in range(2):
        query_text = searchables[i]["text_a"]
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 404

    # Check if objects can are found by their names and descriptions
    for f in ("name", "descr"):
        for i, w in enumerate(("first", "second")):
            object_id = i + 1
            query_text = f"updated {w} {f}"
            body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
            resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
            assert resp.status == 200
            resp_json = await resp.json()
            assert resp_json["items"] == [{"item_id": object_id, "item_type": "object"}]


async def test_add_object_data_link(cli_with_search, db_cursor):
    # Add an object
    obj = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    obj["object_data"]["link"] = "https://new.link.value"
    resp = await cli_with_search.post("/objects/add", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute("SELECT * FROM searchables WHERE object_id = 1")
        return bool(db_cursor.fetchone())

    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if object can be found by its link value
    body = {"query": {"query_text": "new.link.value", "page": 1, "items_per_page": 10}}
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert resp_json["items"] == [{"item_id": 1, "item_type": "object"}]


async def test_add_object_data_markdown(cli_with_search, db_cursor):
    # Add an object
    obj = get_test_object(1, object_type="markdown", pop_keys=["object_id", "created_at", "modified_at"])
    obj["object_data"]["raw_text"] = "# Header text"
    resp = await cli_with_search.post("/objects/add", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute("SELECT * FROM searchables WHERE object_id = 1")
        return bool(db_cursor.fetchone())

    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if object can be found by its Markdown text
    body = {"query": {"query_text": "Header text", "page": 1, "items_per_page": 10}}
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert resp_json["items"] == [{"item_id": 1, "item_type": "object"}]


async def test_add_object_data_to_do_list(cli_with_search, db_cursor):
    # Add an object
    obj = get_test_object(1, object_type="to_do_list", pop_keys=["object_id", "created_at", "modified_at"])
    obj["object_data"]["items"] = [{
        "item_number": 1,
        "item_state": "active",
        "item_text": "To-do list item",
        "commentary": "To-do list commentary",
        "indent": 0,
        "is_expanded": True
    }]
    resp = await cli_with_search.post("/objects/add", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute("SELECT * FROM searchables WHERE object_id = 1")
        return bool(db_cursor.fetchone())

    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if object can be found by its item value and commentary
    for query_text in ("To-do list item", "To-do list commentary"):
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 200
        resp_json = await resp.json()
        assert resp_json["items"] == [{"item_id": 1, "item_type": "object"}]


if __name__ == "__main__":
    run_pytest_tests(__file__)
