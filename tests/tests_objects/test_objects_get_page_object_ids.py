from copy import deepcopy

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.objects import get_test_object, get_objects_attributes_list, insert_objects, \
    insert_data_for_view_tests_objects_with_non_published_tags
from tests.fixtures.db_operations.objects_tags import insert_objects_tags

from tests.fixtures.data_sets.tags import tag_list
from tests.fixtures.db_operations.tags import insert_tags

from tests.fixtures.data_generators.sessions import headers_admin_token


pagination_info = {
    "pagination_info": {
        "page": 1, 
        "items_per_page": 2, 
        "order_by": "object_name", 
        "sort_order": "asc", 
        "filter_text": "", 
        "object_types": ["link"], 
        "tags_filter": [],
        "show_only_displayed_in_feed": False
}}
required_attributes = ("page", "items_per_page", "order_by", "sort_order")
pagination_info_basic = {"pagination_info": {attr: pagination_info["pagination_info"][attr] for attr in required_attributes}}


async def test_incorrect_request_body(cli):
    # Incorrect request body (not a json, missing attributes, wrong attributes)
    resp = await cli.post("/objects/get_page_object_ids", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for attr in required_attributes:
        pi = deepcopy(pagination_info)
        pi["pagination_info"].pop(attr)
        resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect param values
    for k, v in [("page", "text"), ("page", -1), 
        ("items_per_page", "text"), ("items_per_page", -1), 
        ("order_by", 1), ("order_by", "wrong text"),
        ("sort_order", 1), ("sort_order", "wrong text"), 
        ("filter_text", 1), ("filter_text", True), 
        ("object_types", "not a list"), ("object_types", ["wrong object type"]),
        ("tags_filter", 1), ("tags_filter", "string"), ("tags_filter", [1, 2, -1]), ("tags_filter", [1, 2, "not a number"]),
        ("show_only_displayed_in_feed", 1), ("show_only_displayed_in_feed", "str")]:
        pi = deepcopy(pagination_info)
        pi["pagination_info"][k] = v
        resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
        assert resp.status == 400


async def test_correct_request_sort_by_name(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)
    insert_objects(obj_list, db_cursor)

    # Correct request - sort by object_name asc + check response body
    pi = deepcopy(pagination_info_basic)
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "pagination_info" in data
    for attr in pagination_info["pagination_info"]:
        assert attr in data["pagination_info"] or attr not in required_attributes
        assert data["pagination_info"].get(attr) == pi["pagination_info"].get(attr) or attr not in required_attributes
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2] # a0, b1

    # Correct request - sort by object_name desc
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [10, 9] # j1, h0


async def test_correct_request_sort_by_modified_at(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)
    insert_objects(obj_list, db_cursor)

    # Correct request - sort by modified_at asc
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["order_by"] = "modified_at"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [8, 4]

    # Correct request - sort by modified_at desc + query second page
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["page"] = 2
    pi["pagination_info"]["order_by"] = "modified_at"
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [7, 6]


async def test_correct_request_sort_by_feed_timestamp(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)
    insert_objects(obj_list, db_cursor)

    """
    Sort by feed_timestamp asc order (for object IDs 1 to 10):
    7 3 8 4 2 6 10 1 5 9

    Even numbers don't have feed_timestamp set, so use modified_at instead, which is offset by minutes, rather than days, as are set `feed_timestamp` values.
    """
    # Correct request - sort by feed_timestamp asc
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["order_by"] = "feed_timestamp"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)

    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [7, 3]

    # Correct request - sort by feed_timestamp desc + query second page
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["order_by"] = "feed_timestamp"
    pi["pagination_info"]["sort_order"] = "desc"
    pi["pagination_info"]["page"] = 2
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 10]


async def test_correct_request_filter_text(cli, db_cursor):
    # Insert mock values
    obj_list = [
        get_test_object(1, object_name="A-A", owner_id=1),
        get_test_object(2, object_name="BAa", owner_id=1),
        get_test_object(3, object_name="CAa", owner_id=1),
        get_test_object(4, object_name="DAa", owner_id=1),
        get_test_object(5, object_name="EAEa", owner_id=1),
        get_test_object(6, object_name="FAEF", owner_id=1)
    ]
    insert_objects(obj_list, db_cursor)

    # Correct request - no text filter + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - empty string as text filter + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["filter_text"] = ""
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - text filter  + sort by object name asc (also check if filter text case is ignored)
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["filter_text"] = "aA"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == 3
    assert data["pagination_info"]["object_ids"] == [2, 3]

    # Correct request - no matches found
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["filter_text"] = "non-existing object name"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 404


async def test_correct_request_object_types_filter(cli, db_cursor):
    # Insert mock values
    obj_list = [
        get_test_object(1, object_type="link", owner_id=1),
        get_test_object(2, object_type="link", owner_id=1),
        get_test_object(3, object_type="markdown", owner_id=1),
        get_test_object(4, object_type="markdown", owner_id=1),
        get_test_object(5, object_type="to_do_list", owner_id=1),
        get_test_object(6, object_type="to_do_list", owner_id=1)
    ]
    insert_objects(obj_list, db_cursor)

    # Correct request - no objects type filter + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - empty object types filter + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["object_types"] = []
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - object types filter + sort by object name asc
    for object_types, result_object_ids, total_items in ((["link", "markdown"], [1, 2], 4), (["markdown", "to_do_list"], [3, 4], 4)):
        pi = deepcopy(pagination_info_basic)
        pi["pagination_info"]["object_types"] = object_types
        resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
        assert resp.status == 200
        data = await resp.json()
        assert data["pagination_info"]["total_items"] == total_items
        assert data["pagination_info"]["object_ids"] == result_object_ids

    # Correct request - no matches found
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["object_types"] = ["composite"]
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 404


async def test_correct_request_tags_filter(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)
    insert_objects(obj_list, db_cursor)
    insert_tags(tag_list, db_cursor, generate_ids=True)
    insert_objects_tags([5], [1, 2], db_cursor)
    insert_objects_tags([6], [1, 3], db_cursor)
    insert_objects_tags([7, 8], [1, 2, 3], db_cursor)

    # Correct request - no tags filter + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - empty tags filter + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["tags_filter"] = []
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - one tag in tags filter + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["tags_filter"] = [1]
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == 4
    assert data["pagination_info"]["object_ids"] == [5, 6]

    # Correct request - multiple tags in tags filter + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["tags_filter"] = [1, 2, 3]
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == 2
    assert data["pagination_info"]["object_ids"] == [7, 8]

    # Correct request - no matches found
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["tags_filter"] = [4]
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 404


async def test_correct_request_show_only_displayed_in_feed(cli, db_cursor):
    # Insert mock values
    obj_list = [
        get_test_object(1, object_type="link", display_in_feed=False, owner_id=1),
        get_test_object(2, object_type="link", display_in_feed=False, owner_id=1),
        get_test_object(3, object_type="link", display_in_feed=True, owner_id=1),
        get_test_object(4, object_type="link", display_in_feed=True, owner_id=1)
    ]
    insert_objects(obj_list, db_cursor)

    # Correct request - no show_only_displayed_in_feed + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - show_only_displayed_in_feed = False + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["show_only_displayed_in_feed"] = False
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - show_only_displayed_in_feed = True + sort by object name asc
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["show_only_displayed_in_feed"] = True
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == 2
    assert data["pagination_info"]["object_ids"] == [3, 4]

    # Correct request - show_only_displayed_in_feed = True + no matches
    pi = deepcopy(pagination_info_basic)
    pi["pagination_info"]["show_only_displayed_in_feed"] = True
    pi["pagination_info"]["object_types"] = ["composite"]
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 404
    

async def test_correct_request_objects_with_non_published_tags(cli, db_cursor):
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor)
    expected_object_ids = inserts["inserted_object_ids"]

    # Get all objects on one page (and receive only objects without non-published tags)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["items_per_page"] = 10
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(expected_object_ids)
    assert sorted(data["pagination_info"]["object_ids"]) == expected_object_ids


if __name__ == "__main__":
    run_pytest_tests(__file__)
