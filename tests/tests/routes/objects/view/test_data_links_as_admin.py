"""
Tests for link-specific operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_objects_attributes_list
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.objects import links_data_list, insert_data_for_view_tests_objects_with_non_published_tags

from tests.db_operations.objects import insert_objects, insert_links

from tests.request_generators.objects import get_objects_view_request_body

from tests.util import ensure_equal_collection_elements


async def test_view_non_published_objects(cli, db_cursor):
    # Insert mock values
    insert_objects(get_objects_attributes_list(1, 10), db_cursor)
    insert_links(links_data_list, db_cursor)

    # Correct request (object_data_ids only, links), non-existing ids
    object_data_ids = [_ for _ in range(1001, 1011)]
    body = get_objects_view_request_body(object_ids=[], object_data_ids=object_data_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 404
    
    # Correct request (object_data_ids only, links)
    object_data_ids = [_ for _ in range(1, 11)]
    body = get_objects_view_request_body(object_ids=[], object_data_ids=object_data_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "objects_data" in data

    for field in ("object_id", "object_type", "object_data"):
        assert field in data["objects_data"][0]
    for field in ("link", "show_description_as_link"):
        assert field in data["objects_data"][0]["object_data"]

    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    ensure_equal_collection_elements(object_data_ids, received_objects_data_ids,
        "Objects view, correct request as admin, link object_data_ids only")


async def test_view_objects_with_non_published_tags(cli, db_cursor):
    # Insert data (published objects with published & non-published tags)
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor, object_type="link")
    requested_object_ids = inserts["inserted_object_ids"]

    # Correct request (object_ids only)
    body = get_objects_view_request_body(object_ids=[], object_data_ids=requested_object_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    ensure_equal_collection_elements(requested_object_ids, received_objects_data_ids,
        "Objects view, correct request as admin, link object_data_ids only")


if __name__ == "__main__":
    run_pytest_tests(__file__)
