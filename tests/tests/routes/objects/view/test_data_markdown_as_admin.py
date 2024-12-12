"""
Tests for markdown-specific operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.objects import get_objects_attributes_list
from tests.fixtures.data_generators.sessions import headers_admin_token

from tests.fixtures.data_sets.objects import markdown_data_list, insert_data_for_view_tests_objects_with_non_published_tags

from tests.fixtures.db_operations.objects import insert_objects, insert_markdown

from tests.util import ensure_equal_collection_elements


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

    ensure_equal_collection_elements(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as admin, markdown object_data_ids only")


async def test_view_objects_with_non_published_tags(cli, db_cursor):
    # Insert data (published objects with published & non-published tags)
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor, object_type="markdown")
    requested_object_ids = inserts["inserted_object_ids"]

    # Correct request (object_ids only)
    resp = await cli.post("/objects/view", json={"object_data_ids": requested_object_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    ensure_equal_collection_elements(requested_object_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as admin, markdown object_data_ids only")


if __name__ == "__main__":
    run_pytest_tests(__file__)
