from copy import deepcopy

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag
from tests.data_sets.tags import tag_list
from tests.db_operations.tags import insert_tags, delete_tags
from tests.request_generators.tags import get_page_tag_ids_request_body


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.post("/tags/get_page_tag_ids", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for attr in ("page", "items_per_page", "order_by", "sort_order", "filter_text"):
        pi = get_page_tag_ids_request_body()
        pi["pagination_info"].pop(attr)
        resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect param values
    incorrect_values = {
        "page": ["a", {}, [], -1, 0],
        "items_per_page": ["a", {}, [], -1, 0],
        "order_by": [1, False, {}, [], "wrong text"],
        "sort_order": [1, False, {}, [], "wrong text"],
        "filter_text": [1, False, {}, [], "a" * 256]
    }
    for attr, values in incorrect_values.items():
        for value in values:
            pi = get_page_tag_ids_request_body()
            pi["pagination_info"][attr] = value
            resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
            assert resp.status == 400


async def test_correct_request_tag_name_asc(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)
    
    # Send request & check response
    pi = get_page_tag_ids_request_body()
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    for attr in ["page", "items_per_page","total_items", "order_by", "sort_order", "filter_text", "tag_ids"]:
        assert attr in data
        assert data[attr] == pi["pagination_info"].get(attr, None) or attr in ["total_items", "tag_ids"]
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [1, 2] # a0, b1


async def test_correct_request_tag_name_desc(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)

    # Send request & check response
    pi = get_page_tag_ids_request_body()
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [10, 9] # j1, h0


async def test_correct_request_modified_at_asc(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)

    # Send request & check response
    pi = get_page_tag_ids_request_body()
    pi["pagination_info"]["order_by"] = "modified_at"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [1, 5] # a0, e0


async def test_correct_request_modified_at_desc_second_page(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)

    # Send request & check response
    pi = get_page_tag_ids_request_body()
    pi["pagination_info"]["page"] = 2
    pi["pagination_info"]["order_by"] = "modified_at"
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [7, 6] # g0, f1


async def test_correct_request_filter_text(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)

    # Send request & check response
    pi = get_page_tag_ids_request_body()
    pi["pagination_info"]["filter_text"] = "0"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list) // 2
    assert data["tag_ids"] == [1, 3] # a0, c0

    # Filter by text + check if filter_text case is ignored
    insert_tags([get_test_tag(100, "aa"), get_test_tag(101, "AaA"), get_test_tag(102, "AAaa"), get_test_tag(103, "aaaAa")], db_cursor)
    pi = get_page_tag_ids_request_body()
    pi["pagination_info"]["filter_text"] = "aA"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == 4 # id = [100, 101, 102, 103]
    assert data["tag_ids"] == [100, 101]
    delete_tags([100, 101, 102, 103], db_cursor)


async def test_correct_request_non_published_tags(cli, db_cursor):
    # Insert data
    insert_tags([
        get_test_tag(1, tag_name="a1", is_published=False),
        get_test_tag(2, tag_name="a2", is_published=True),
        get_test_tag(3, tag_name="a3", is_published=False),
        get_test_tag(4, tag_name="a4", is_published=True),
        get_test_tag(7, tag_name="b1", is_published=True),
        get_test_tag(8, tag_name="b2", is_published=False)
    ], db_cursor)
    
    # Send request & check response (tags are returned regardless of their `is_published` prop)
    pi = get_page_tag_ids_request_body()
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    for attr in ["page", "items_per_page","total_items", "order_by", "sort_order", "filter_text", "tag_ids"]:
        assert attr in data
        assert data[attr] == pi["pagination_info"].get(attr, None) or attr in ["total_items", "tag_ids"]
    assert data["total_items"] == 6
    assert data["tag_ids"] == [1, 2] # a1, a2


if __name__ == "__main__":
    run_pytest_tests(__file__)
