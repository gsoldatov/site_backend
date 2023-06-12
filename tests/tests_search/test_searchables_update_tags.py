"""
Tests for automatic tag processing after route handler execution.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from datetime import datetime

from tests.fixtures.objects import get_test_object, get_test_object_data, insert_objects, insert_links
from tests.fixtures.sessions import headers_admin_token
from tests.fixtures.searchables import get_test_searchable, insert_searchables
from tests.fixtures.tags import get_test_tag, insert_tags

from tests.util import wait_for


async def test_add_tag(cli_with_search, db_cursor):
    # Add 2 tags
    for w in ("first", "second"):
        tag = get_test_tag(1, tag_name=f"{w} name", tag_description=f"{w} descr", pop_keys=["tag_id", "created_at", "modified_at"])
        resp = await cli_with_search.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 200

    # Wait for tag searchables to be added
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables")
        return db_cursor.fetchone()[0] == 2

    await wait_for(fn, msg="Tag searchables were not processed in time.")

    # Check if tags can are found by their names and descriptions
    for f in ("name", "descr"):
        for i, w in enumerate(("first", "second")):
            tag_id = i + 1
            query_text = f"{w} {f}"
            body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
            resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
            assert resp.status == 200
            resp_json = await resp.json()
            assert resp_json["items"] == [{"item_id": tag_id, "item_type": "tag"}]


async def test_update_tag(cli_with_search, db_cursor):
    # Insert mock values
    tag_list = [get_test_tag(1), get_test_tag(2)]
    insert_tags(tag_list, db_cursor)
    old_modified_at = datetime(2001, 1, 1)
    searchables = [get_test_searchable(tag_id=i+1, text_a=f"old {w}", modified_at=old_modified_at) for i,w in enumerate(("first", "second"))]
    insert_searchables(searchables, db_cursor)

    # Update both tags
    for i, w in enumerate(("first", "second")):
        tag = get_test_tag(i + 1, tag_name=f"updated {w} name", tag_description=f"updated {w} descr", pop_keys=["created_at", "modified_at"])
        resp = await cli_with_search.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 200

    # Wait for tag searchables to be updated
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables WHERE modified_at > %(old_modified_at)s", {"old_modified_at": old_modified_at})
        return db_cursor.fetchone()[0] == 2

    await wait_for(fn, msg="Tag searchables were not processed in time.")

    # Check if old searchables are no longer present
    for i in range(2):
        query_text = searchables[i]["text_a"]
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 404

    # Check if tags can are found by their names and descriptions
    for f in ("name", "descr"):
        for i, w in enumerate(("first", "second")):
            tag_id = i + 1
            query_text = f"updated {w} {f}"
            body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
            resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
            assert resp.status == 200
            resp_json = await resp.json()
            assert resp_json["items"] == [{"item_id": tag_id, "item_type": "tag"}]


async def test_add_object_with_new_tags(cli_with_search, db_cursor):
    # Add an object with new tags
    link = get_test_object(2, pop_keys=["object_id", "created_at", "modified_at"])
    link["added_tags"] = ["first tag", "second tag"]
    resp = await cli_with_search.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for tag searchables to be added
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables WHERE NOT tag_id ISNULL")
        return db_cursor.fetchone()[0] == 2

    await wait_for(fn, msg="Tag searchables were not processed in time.")

    # Check if tags can are found by their names
    for i, w in enumerate(("first", "second")):
        tag_id = i + 1
        query_text = f"{w} tag"
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 200
        resp_json = await resp.json()
        assert resp_json["items"] == [{"item_id": tag_id, "item_type": "tag"}]


async def test_update_object_with_new_tags(cli_with_search, db_cursor):
    # Insert an object
    insert_objects([get_test_object(1, owner_id=1, pop_keys=["object_data"])], db_cursor)
    insert_links([get_test_object_data(1)], db_cursor)

    # Add an object with new tags
    link = get_test_object(1, object_name="updated object name", pop_keys=["object_type", "created_at", "modified_at"])
    link["added_tags"] = ["first tag", "second tag"]
    resp = await cli_with_search.put("/objects/update", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for tag searchables to be added
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables WHERE NOT tag_id ISNULL")
        return db_cursor.fetchone()[0] == 2

    await wait_for(fn, msg="Tag searchables were not processed in time.")

    # Check if tags can are found by their names
    for i, w in enumerate(("first", "second")):
        tag_id = i + 1
        query_text = f"{w} tag"
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 200
        resp_json = await resp.json()
        assert resp_json["items"] == [{"item_id": tag_id, "item_type": "tag"}]


if __name__ == "__main__":
    run_pytest_tests(__file__)
