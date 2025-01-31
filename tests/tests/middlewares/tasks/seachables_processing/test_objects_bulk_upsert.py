"""
Tests for processing of searchable data from objects passed to /objects/bulk_upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests    

from datetime import datetime

from tests.data_generators.objects import get_test_object, get_test_object_data, get_link_data, \
    get_markdown_data, get_to_do_list_data, get_to_do_list_item_data
from tests.data_generators.searchables import get_test_searchable
from tests.data_generators.sessions import headers_admin_token

from tests.db_operations.objects import insert_objects, insert_links, insert_markdown, insert_to_do_lists
from tests.db_operations.searchables import insert_searchables

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object

from tests.util import wait_for


async def test_upserted_objects_attributes(cli_with_search, db_cursor):
    # Insert existing objects and searchables
    insert_objects([
        get_test_object(i, object_name=f"old name {i}", object_description=f"old description {i}",
                        owner_id=1, pop_keys=["object_data"])
        for i in range(1, 3)
    ], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(i) for i in range(1, 3)], db_cursor)

    old_modified_at = datetime(2001, 1, 1)
    searchables = [get_test_searchable(
        object_id=i, text_a=f"old name {i}", text_b=f"old description {i}",
        modified_at=old_modified_at
    ) for i in range(1, 3)]
    insert_searchables(searchables, db_cursor)

    # Upsert a new & one of existing objects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_name="new name", object_description="new description"),
        get_bulk_upsert_object(object_id=1, object_name="updated name", object_description="updated description")
    ])
    resp = await cli_with_search.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute(f"SELECT COUNT(*) FROM searchables WHERE modified_at > '{old_modified_at.isoformat()}'")
        return db_cursor.fetchone()[0] == 2

    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if objects can be found by their names and descriptions
    # (including non updated existing object)
    for query_text, expected_object_id in [
        ("new name", 3), ("new description", 3),
        ("updated name", 1), ("updated description", 1),
        ("old name 2", 2), ("old description 2", 2),
    ]:
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 200
        resp_json = await resp.json()
        assert resp_json["items"] == [{"item_id": expected_object_id, "item_type": "object"}]
    
    # Check if old searchable data of the updated object is no longer available
    for query_text in ["old name 1", "old description 1"]:
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 404


async def test_upserted_links(cli_with_search, db_cursor):
    # Insert existing objects and searchables
    insert_objects([get_test_object(i, owner_id=1, pop_keys=["object_data"])
        for i in range(1, 3)], db_cursor, generate_ids=True)
    insert_links([{
        "object_id": i,
        "object_data": get_link_data(link=f"https://old.link{i}.com")
    } for i in range(1, 3)], db_cursor)

    old_modified_at = datetime(2001, 1, 1)
    searchables = [get_test_searchable(
        object_id=i, text_b=f"old.link{i}.com",
        modified_at=old_modified_at
    ) for i in range(1, 3)]
    insert_searchables(searchables, db_cursor)

    # Upsert a new & one of existing objects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_data=get_link_data(link="https://new.link.com")),
        get_bulk_upsert_object(object_id=1, object_data=get_link_data(link="https://updated.link.com")),
    ])
    resp = await cli_with_search.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute(f"SELECT COUNT(*) FROM searchables WHERE modified_at > '{old_modified_at.isoformat()}'")
        return db_cursor.fetchone()[0] == 2

    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if objects can be found by their links
    # (including non updated existing object)
    for query_text, expected_object_id in [("new.link.com", 3), ("updated.link.com", 1), ("old.link2.com", 2)]:
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 200
        resp_json = await resp.json()
        assert resp_json["items"] == [{"item_id": expected_object_id, "item_type": "object"}]
    
    # Check if old searchable data of the updated object is no longer available
    for query_text in ["old.link1.com"]:
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 404


async def test_upserted_markdown(cli_with_search, db_cursor):
    # Insert existing objects and searchables
    insert_objects([get_test_object(i, object_type="markdown", owner_id=1, pop_keys=["object_data"])
        for i in range(1, 3)], db_cursor, generate_ids=True)
    insert_markdown([{
        "object_id": i,
        "object_data": get_markdown_data(raw_text=f"old markdown {i}")
    } for i in range(1, 3)], db_cursor)

    old_modified_at = datetime(2001, 1, 1)
    searchables = [get_test_searchable(
        object_id=i, text_b=f"old markdown {i}",
        modified_at=old_modified_at
    ) for i in range(1, 3)]
    insert_searchables(searchables, db_cursor)

    # Upsert a new & one of existing objects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_type="markdown", 
                               object_data=get_markdown_data(raw_text="new markdown")),
        get_bulk_upsert_object(object_id=1, object_type="markdown", 
                               object_data=get_markdown_data(raw_text="updated markdown")),
    ])
    resp = await cli_with_search.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute(f"SELECT COUNT(*) FROM searchables WHERE modified_at > '{old_modified_at.isoformat()}'")
        return db_cursor.fetchone()[0] == 2

    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if objects can be found by their markdown
    # (including non updated existing object)
    for query_text, expected_object_id in [("new markdown", 3), ("updated markdown", 1), ("old markdown 2", 2)]:
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 200
        resp_json = await resp.json()
        assert resp_json["items"] == [{"item_id": expected_object_id, "item_type": "object"}]
    
    # Check if old searchable data of the updated object is no longer available
    for query_text in ["old markdown 1"]:
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 404


async def test_upserted_to_do_lists(cli_with_search, db_cursor):
    # Insert existing objects and searchables
    insert_objects([get_test_object(i, object_type="to_do_list", owner_id=1, pop_keys=["object_data"])
        for i in range(1, 3)], db_cursor, generate_ids=True)
    insert_to_do_lists([{
        "object_id": i,
        "object_data": get_to_do_list_data(
            items=[
                get_to_do_list_item_data(item_text=f"old item {i}", commentary=f"old commentary {i}")
            ]
        )
    } for i in range(1, 3)], db_cursor)

    old_modified_at = datetime(2001, 1, 1)
    searchables = [get_test_searchable(
        object_id=i, text_b=f"old item {i}", text_c=f"old commentary {i}",
        modified_at=old_modified_at
    ) for i in range(1, 3)]
    insert_searchables(searchables, db_cursor)

    # Upsert a new & one of existing objects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_type="to_do_list", object_data=get_to_do_list_data(
            items=[get_to_do_list_item_data(item_text="new item", commentary="new commentary")]
        )),
        get_bulk_upsert_object(object_id=1, object_type="to_do_list", object_data=get_to_do_list_data(
            items=[get_to_do_list_item_data(item_text="updated item", commentary="updated commentary")]
        )),
    ])
    resp = await cli_with_search.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute(f"SELECT COUNT(*) FROM searchables WHERE modified_at > '{old_modified_at.isoformat()}'")
        return db_cursor.fetchone()[0] == 2

    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if objects can be found by their item text and commentary
    # (including non updated existing object)
    for query_text, expected_object_id in [
        ("new item", 3), ("new commentary", 3),
        ("updated item", 1), ("updated commentary", 1),
        ("old item 2", 2), ("old commentary 2", 2)
    ]:
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 200
        resp_json = await resp.json()
        assert resp_json["items"] == [{"item_id": expected_object_id, "item_type": "object"}]
    
    # Check if old searchable data of the updated object is no longer available
    for query_text in ["old item 1", "old commentary 1"]:
        body = {"query": {"query_text": query_text, "page": 1, "items_per_page": 10}}
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 404


if __name__ == "__main__":
    run_pytest_tests(__file__)
