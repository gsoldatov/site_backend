"""
Basic search, pagination and ranking tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.objects import get_test_object, insert_objects
from tests.fixtures.searchables import get_test_searchable, insert_searchables
from tests.fixtures.tags import get_test_tag, insert_tags



async def test_correct_search(cli_with_search, db_cursor):
    # Insert mock data
    obj_list = [get_test_object(i + 1, object_type="link", owner_id=1, is_published=bool(i % 2), pop_keys=["object_data"]) for i in range(20)]
    insert_objects(obj_list, db_cursor)

    searchables = [get_test_searchable(object_id=i + 1, text_a="word" if i < 10 else "bird") for i in range(20)]
    insert_searchables(searchables, db_cursor)

    tag_list = [get_test_tag(i + 1) for i in range(10)]
    insert_tags(tag_list, db_cursor)

    searchables = [get_test_searchable(tag_id=i + 1, text_a="word" if i < 5 else "bird") for i in range(10)]
    insert_searchables(searchables, db_cursor)

    # Check if matching tags and published objects are returned
    body = {"query": {"query_text": "word", "page": 1, "items_per_page": 100}}
    resp = await cli_with_search.post("/search", json=body)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 5 + 5

    object_ids = [item["item_id"] for item in resp_json["items"] if item["item_type"] == "object"]
    assert sorted(object_ids) == [2, 4, 6, 8, 10]

    tag_ids = [item["item_id"] for item in resp_json["items"] if item["item_type"] == "tag"]
    assert sorted(tag_ids) == [1, 2, 3, 4, 5]


if __name__ == "__main__":
    run_pytest_tests(__file__)
