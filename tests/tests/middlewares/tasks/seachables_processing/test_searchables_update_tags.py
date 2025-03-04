"""
Tests for processing of searchable data from added or updated tags.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from datetime import datetime

from tests.data_generators.objects import get_test_object, get_object_attrs, get_test_object_data
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.searchables import get_test_searchable
from tests.data_generators.tags import get_test_tag

from tests.db_operations.objects import insert_objects, insert_links
from tests.db_operations.searchables import insert_searchables
from tests.db_operations.tags import insert_tags

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object
from tests.request_generators.tags import get_tags_add_request_body, get_tags_update_request_body

from tests.util import wait_for


async def test_tags_add(cli_with_search, db_cursor):
    # Add 2 tags
    for w in ("first", "second"):
        body = get_tags_add_request_body(tag_name=f"{w} name", tag_description=f"{w} descr")
        resp = await cli_with_search.post("/tags/add", json=body, headers=headers_admin_token)
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


async def test_tags_update(cli_with_search, db_cursor):
    # Insert mock values
    tag_list = [get_test_tag(1), get_test_tag(2)]
    insert_tags(tag_list, db_cursor)
    old_modified_at = datetime(2001, 1, 1)
    searchables = [get_test_searchable(tag_id=i+1, text_a=f"old {w}", modified_at=old_modified_at) for i,w in enumerate(("first", "second"))]
    insert_searchables(searchables, db_cursor)

    # Update both tags
    for i, w in enumerate(("first", "second")):
        body = get_tags_update_request_body(tag_id=i + 1, tag_name=f"updated {w} name", tag_description=f"updated {w} descr")
        resp = await cli_with_search.put("/tags/update", json=body, headers=headers_admin_token)
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


async def test_objects_add(cli_with_search, db_cursor):
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

        # NOTE: id order is not guaranteed to match the order of new tags in request body
        # due to deduplication
        # assert resp_json["items"] == [{"item_id": tag_id, "item_type": "tag"}]
        assert len(resp_json["items"]) == 1
        assert resp_json["items"][0]["item_type"] == "tag"


async def test_objects_update(cli_with_search, db_cursor):
    # Insert an object
    insert_objects([get_object_attrs(1)], db_cursor)
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

        # NOTE: id order is not guaranteed to match the order of new tags in request body
        # due to deduplication
        # assert resp_json["items"] == [{"item_id": tag_id, "item_type": "tag"}]
        assert len(resp_json["items"]) == 1
        assert resp_json["items"][0]["item_type"] == "tag"


async def test_objects_bulk_upsert(cli_with_search, db_cursor):
    # Insert an object
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(1)], db_cursor)

    # Upsert a new & update an existing object and add string tags
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, added_tags=["first tag"]),
        get_bulk_upsert_object(object_id=1, added_tags=["second tag"])
    ])
    resp = await cli_with_search.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
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

        # NOTE: id order is not guaranteed to match the order of new tags in request body
        # due to deduplication
        # assert resp_json["items"] == [{"item_id": tag_id, "item_type": "tag"}]
        assert len(resp_json["items"]) == 1
        assert resp_json["items"][0]["item_type"] == "tag"


if __name__ == "__main__":
    run_pytest_tests(__file__)
