"""
Basic search, pagination and ranking tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 5)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.objects import get_test_object
from tests.fixtures.data_generators.searchables import get_test_searchable
from tests.fixtures.data_generators.tags import get_test_tag

from tests.fixtures.db_operations.objects import insert_objects
from tests.fixtures.db_operations.objects_tags import insert_objects_tags
from tests.fixtures.db_operations.searchables import insert_searchables
from tests.fixtures.db_operations.tags import insert_tags


async def test_correct_search_non_published_objects(cli_with_search, db_cursor):
    # Insert mock data
    obj_list = [get_test_object(i + 1, object_type="link", owner_id=1, is_published=bool(i % 2), pop_keys=["object_data"]) for i in range(20)]
    insert_objects(obj_list, db_cursor)

    searchables = [get_test_searchable(object_id=i + 1, text_a="word" if i < 10 else "bird") for i in range(20)]
    insert_searchables(searchables, db_cursor)

    # Check if matching published objects are returned
    body = {"query": {"query_text": "word", "page": 1, "items_per_page": 100}}
    resp = await cli_with_search.post("/search", json=body)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 5

    object_ids = [item["item_id"] for item in resp_json["items"] if item["item_type"] == "object"]
    assert sorted(object_ids) == [2, 4, 6, 8, 10]


async def test_correct_search_non_published_tags(cli_with_search, db_cursor):
    tag_list = [get_test_tag(i + 1, is_published=bool(i % 2)) for i in range(20)]
    insert_tags(tag_list, db_cursor)

    searchables = [get_test_searchable(tag_id=i + 1, text_a="word" if i < 10 else "bird") for i in range(10)]
    insert_searchables(searchables, db_cursor)

    # Check if matching published tags are returned
    body = {"query": {"query_text": "word", "page": 1, "items_per_page": 100}}
    resp = await cli_with_search.post("/search", json=body)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 5

    tag_ids = [item["item_id"] for item in resp_json["items"] if item["item_type"] == "tag"]
    assert sorted(tag_ids) == [2, 4, 6, 8, 10]


async def test_correct_search_objects_with_non_published_tags(cli_with_search, db_cursor):
    # Insert mock data
    obj_list = [get_test_object(i + 1, object_type="link", owner_id=1, is_published=bool(i % 2), pop_keys=["object_data"]) for i in range(20)]
    insert_objects(obj_list, db_cursor)

    searchables = [get_test_searchable(object_id=i + 1, text_a="word" if i < 10 else "bird") for i in range(20)]
    insert_searchables(searchables, db_cursor)

    tag_list = [get_test_tag(i + 1, is_published=bool(i < 1)) for i in range(3)]
    insert_tags(tag_list, db_cursor)

    searchables = [get_test_searchable(tag_id=i + 1, text_a="bird") for i in range(3)]
    insert_searchables(searchables, db_cursor)

    insert_objects_tags([i for i in range(1, 11)], [1], db_cursor)
    insert_objects_tags([i for i in range(6, 11)], [2], db_cursor)
    insert_objects_tags([i for i in range(9, 11)], [3], db_cursor)

    # Check if matching published objects not tagged with non-published tags are returned
    body = {"query": {"query_text": "word", "page": 1, "items_per_page": 100}}
    resp = await cli_with_search.post("/search", json=body)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 2

    object_ids = [item["item_id"] for item in resp_json["items"] if item["item_type"] == "object"]
    assert sorted(object_ids) == [2, 4]


if __name__ == "__main__":
    run_pytest_tests(__file__)
