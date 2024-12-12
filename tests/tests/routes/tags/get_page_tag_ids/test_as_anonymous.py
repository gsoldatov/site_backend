from copy import deepcopy

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_sets.tags import tag_list

from tests.db_operations.tags import insert_tags


pagination_info = {"pagination_info": {"page": 1, "items_per_page": 2, "order_by": "tag_name", "sort_order": "asc", "filter_text": ""}}


async def test_correct_request_tag_name_asc(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)
    
    # Send request & check response
    pi = deepcopy(pagination_info)
    resp = await cli.post("/tags/get_page_tag_ids", json=pi)
    assert resp.status == 200
    data = await resp.json()
    for attr in ["page", "items_per_page","total_items", "order_by", "sort_order", "filter_text", "tag_ids"]:
        assert attr in data
        assert data[attr] == pi["pagination_info"].get(attr, None) or attr in ["total_items", "tag_ids"]

    # Check if only published tags are returned
    assert data["total_items"] == len(tag_list) // 2
    assert data["tag_ids"] == [1, 3] # a0, c0


if __name__ == "__main__":
    run_pytest_tests(__file__)
