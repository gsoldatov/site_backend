from copy import deepcopy

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.tags import get_test_tag, tag_list, insert_tags, delete_tags


pagination_info = {"pagination_info": {"page": 1, "items_per_page": 2, "order_by": "tag_name", "sort_order": "asc", "filter_text": ""}}


async def test_correct_requests(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)
    
    # Correct request - sort by tag_name asc + response body
    pi = deepcopy(pagination_info)
    resp = await cli.post("/tags/get_page_tag_ids", json=pi)
    assert resp.status == 200
    data = await resp.json()
    for attr in ["page", "items_per_page","total_items", "order_by", "sort_order", "filter_text", "tag_ids"]:
        assert attr in data
        assert data[attr] == pi["pagination_info"].get(attr, None) or attr in ["total_items", "tag_ids"]
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [1, 2] # a0, b1

    # Correct request - sort by tag_name desc
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [10, 9] # j1, h0

    # Correct request - sort by modified_at asc
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["order_by"] = "modified_at"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [1, 5] # a0, e0

    # Correct request - sort by modified_at desc + second page
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["page"] = 2
    pi["pagination_info"]["order_by"] = "modified_at"
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [7, 6] # g0, f1

    # Correct request - sort by tag_name asc with filter text
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["filter_text"] = "0"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list) // 2
    assert data["tag_ids"] == [1, 3] # a0, c0

    # Correct request - filter by text + check if filter_text case is ignored
    insert_tags([get_test_tag(100, "aa"), get_test_tag(101, "AaA"), get_test_tag(102, "AAaa"), get_test_tag(103, "aaaAa")], db_cursor)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["filter_text"] = "aA"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == 4 # id = [100, 101, 102, 103]
    assert data["tag_ids"] == [100, 101]
    delete_tags([100, 101, 102, 103], db_cursor)


if __name__ == "__main__":
    run_pytest_tests(__file__)
