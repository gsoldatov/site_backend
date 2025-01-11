from copy import deepcopy

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_objects_attributes_list
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.objects import insert_data_for_view_tests_objects_with_non_published_tags
from tests.data_sets.tags import tag_list

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags

from tests.request_generators.objects import get_page_object_ids_request_body


async def test_incorrect_request_body(cli):
    # Missing and unallowed top-level attributes
    resp = await cli.post("/objects/get_page_object_ids", data={}, headers=headers_admin_token)
    assert resp.status == 400

    body = get_page_object_ids_request_body()
    body["unallowed"] = 1
    resp = await cli.post("/objects/get_page_object_ids", data=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect pagination info type
    for value in ("a", 1, []):
        resp = await cli.post("/objects/get_page_object_ids", data={"pagination_info": value}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Missing required attributes
    for attr in ("page", "items_per_page", "order_by", "sort_order"):
        body = get_page_object_ids_request_body()
        body["pagination_info"].pop(attr)
        resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect attribute values
    incorrect_attributes = {
        "page": ["a", {}, [], -1, 0],
        "items_per_page": ["a", {}, [], -1, 0],
        "order_by": [1, False, {}, [], "wrong str"],
        "sort_order": [1, False, {}, [], "wrong str"],
        "filter_text": [1, False, {}, [], "a" * 256],
        "object_types": [1, False, {}, "a", [1], ["wrong str"], ["link"] * 5],
        "tags_filter": [1, "a", {}, ["a"], [-1], [0], [1] * 101],
        "show_only_displayed_in_feed": [2, "a", {}, []]
    }
    for attr, values in incorrect_attributes.items():
        for value in values:
            body = get_page_object_ids_request_body()
            body["pagination_info"][attr] = value
            resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
            assert resp.status == 400


async def test_correct_request_sort_by_name(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)
    insert_objects(obj_list, db_cursor)

    # Correct request - sort by object_name asc + check response body
    body = get_page_object_ids_request_body(order_by="object_name", sort_order="asc")
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["order_by"] == "object_name"
    assert data["pagination_info"]["sort_order"] == "asc"
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2] # a0, b1

    # Correct request - sort by object_name desc
    body = get_page_object_ids_request_body(order_by="object_name", sort_order="desc")
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["sort_order"] == "desc"
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [10, 9] # j1, h0


async def test_correct_request_sort_by_modified_at(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)
    insert_objects(obj_list, db_cursor)

    # Correct request - sort by modified_at asc
    body = get_page_object_ids_request_body(order_by="modified_at", sort_order="asc")
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["order_by"] == "modified_at"
    assert data["pagination_info"]["sort_order"] == "asc"
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [8, 4]

    # Correct request - sort by modified_at desc + query second page
    body = get_page_object_ids_request_body(page=2, order_by="modified_at", sort_order="desc")
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["page"] == 2
    assert data["pagination_info"]["sort_order"] == "desc"
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
    body = get_page_object_ids_request_body(order_by="feed_timestamp", sort_order="asc")
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)

    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["order_by"] == "feed_timestamp"
    assert data["pagination_info"]["sort_order"] == "asc"
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [7, 3]

    # Correct request - sort by feed_timestamp desc + query second page
    body = get_page_object_ids_request_body(page=2, order_by="feed_timestamp", sort_order="desc")
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["page"] == 2
    assert data["pagination_info"]["sort_order"] == "desc"
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
    body = get_page_object_ids_request_body()
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["filter_text"] == ""
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - empty string as text filter + sort by object name asc
    body = get_page_object_ids_request_body(filter_text="")
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["filter_text"] == ""
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - text filter  + sort by object name asc (also check if filter text case is ignored)
    body = get_page_object_ids_request_body(filter_text="aA")
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["filter_text"] == "aA"
    assert data["pagination_info"]["total_items"] == 3
    assert data["pagination_info"]["object_ids"] == [2, 3]

    # Correct request - no matches found
    body = get_page_object_ids_request_body(filter_text="non-existing object name")
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
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
    body = get_page_object_ids_request_body()
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["object_types"] == []
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - empty object types filter + sort by object name asc
    body = get_page_object_ids_request_body(object_types=[])
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - object types filter + sort by object name asc
    for object_types, result_object_ids, total_items in \
        ((["link", "markdown"], [1, 2], 4), (["markdown", "to_do_list"], [3, 4], 4)):
        body = get_page_object_ids_request_body(object_types=object_types)
        resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
        assert resp.status == 200
        data = await resp.json()
        assert data["pagination_info"]["object_types"] == object_types
        assert data["pagination_info"]["total_items"] == total_items
        assert data["pagination_info"]["object_ids"] == result_object_ids

    # Correct request - no matches found
    body = get_page_object_ids_request_body(object_types=["composite"])
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
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
    body = get_page_object_ids_request_body()
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["tags_filter"] == []
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - empty tags filter + sort by object name asc
    body = get_page_object_ids_request_body(tags_filter=[])
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - one tag in tags filter + sort by object name asc
    body = get_page_object_ids_request_body(tags_filter=[1])
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["tags_filter"] == [1]
    assert data["pagination_info"]["total_items"] == 4
    assert data["pagination_info"]["object_ids"] == [5, 6]

    # Correct request - multiple tags in tags filter + sort by object name asc
    body = get_page_object_ids_request_body(tags_filter=[1, 2, 3])
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == 2
    assert data["pagination_info"]["object_ids"] == [7, 8]

    # Correct request - no matches found
    body = get_page_object_ids_request_body(tags_filter=[4])
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
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
    body = get_page_object_ids_request_body()
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["show_only_displayed_in_feed"] == False
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - show_only_displayed_in_feed = False + sort by object name asc
    body = get_page_object_ids_request_body(show_only_displayed_in_feed=False)
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(obj_list)
    assert data["pagination_info"]["object_ids"] == [1, 2]

    # Correct request - show_only_displayed_in_feed = True + sort by object name asc
    body = get_page_object_ids_request_body(show_only_displayed_in_feed=True)
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["show_only_displayed_in_feed"] == True
    assert data["pagination_info"]["total_items"] == 2
    assert data["pagination_info"]["object_ids"] == [3, 4]

    # Correct request - show_only_displayed_in_feed = True + no matches
    body = get_page_object_ids_request_body(show_only_displayed_in_feed=True, object_types=["composite"])
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 404
    

async def test_correct_request_objects_with_non_published_tags(cli, db_cursor):
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor)
    expected_object_ids = inserts["inserted_object_ids"]

    # Get all objects on one page (and receive only objects without non-published tags)
    body = get_page_object_ids_request_body(items_per_page=10)
    resp = await cli.post("/objects/get_page_object_ids", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(expected_object_ids)
    assert sorted(data["pagination_info"]["object_ids"]) == expected_object_ids


if __name__ == "__main__":
    run_pytest_tests(__file__)
