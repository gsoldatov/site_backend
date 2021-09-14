from copy import deepcopy

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.fixtures.objects import get_test_object, get_objects_attributes_list, insert_objects, delete_objects, \
    insert_data_for_view_objects_as_anonymous
from tests.fixtures.objects_tags import insert_objects_tags
from tests.fixtures.tags import tag_list, insert_tags
from tests.fixtures.sessions import headers_admin_token


pagination_info = {"pagination_info": {"page": 1, "items_per_page": 2, "order_by": "object_name", "sort_order": "asc", "filter_text": "", "object_types": ["link"], "tags_filter": []}}


async def test_incorrect_request_body_as_admin(cli):
    # Incorrect request body (not a json, missing attributes, wrong attributes)
    resp = await cli.post("/objects/get_page_object_ids", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for attr in pagination_info["pagination_info"]:
        pi = deepcopy(pagination_info)
        pi["pagination_info"].pop(attr)
        resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect param values
    for k, v in [("page", "text"), ("page", -1), ("items_per_page", "text"), ("items_per_page", -1), ("order_by", 1), ("order_by", "wrong text"),
                 ("sort_order", 1), ("sort_order", "wrong text"), ("filter_text", 1), ("object_types", "not a list"), ("object_types", ["wrong object type"]),
                 ("tags_filter", 1), ("tags_filter", "string"), ("tags_filter", [1, 2, -1]), ("tags_filter", [1, 2, "not a number"])]:
        pi = deepcopy(pagination_info)
        pi["pagination_info"][k] = v
        resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
        assert resp.status == 400


async def test_correct_requests_as_admin(cli, db_cursor):
    # Insert mock values
    obj_list = get_objects_attributes_list(1, 10)   # links
    obj_list.extend(get_objects_attributes_list(11, 18)) # markdown
    obj_count = len(obj_list)
    links_count = sum((1 for obj in obj_list if obj["object_type"] == "link"))
    markdown_count = sum((1 for obj in obj_list if obj["object_type"] == "markdown"))

    insert_objects(obj_list, db_cursor)

    insert_tags(tag_list, db_cursor, generate_tag_ids=True)
    insert_objects_tags([_ for _ in range(1, 8)], [1], db_cursor)
    insert_objects_tags([_ for _ in range(5, 11)], [2], db_cursor)
    insert_objects_tags([1, 3, 5, 7, 9], [3], db_cursor)
    insert_objects_tags([11, 12], [1, 2, 3], db_cursor)
    
    # Correct request - sort by object_name asc + check response body (links only)
    pi = deepcopy(pagination_info)
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    for attr in ["page", "items_per_page","total_items", "order_by", "sort_order", "filter_text", "object_types", "object_ids"]:
        assert attr in data
        assert data[attr] == pi["pagination_info"].get(attr, None) or attr in ["object_types", "total_items", "object_ids"]
    assert data["total_items"] == links_count
    assert data["object_ids"] == [1, 2] # a0, b1

    # Correct request - sort by object_name desc (links only)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [10, 9] # j1, h0

    # Correct request - sort by modified_at asc (links only)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["order_by"] = "modified_at"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [8, 4]

    # Correct request - sort by modified_at desc + query second page (links only)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["page"] = 2
    pi["pagination_info"]["order_by"] = "modified_at"
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [7, 6]

    # Correct request - filter by text (links only)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["filter_text"] = "0"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count // 2
    assert data["object_ids"] == [1, 3] # a0, c0

    # Correct request - filter by text + check if filter_text case is ignored (links only)
    insert_objects([get_test_object(100, owner_id=1, object_type="link", object_name="aa", pop_keys=["object_data"]), 
                    get_test_object(101, owner_id=1, object_type="link", object_name="AaA", pop_keys=["object_data"]),
                    get_test_object(102, owner_id=1, object_type="link", object_name="AAaa", pop_keys=["object_data"]), 
                    get_test_object(103, owner_id=1, object_type="link", object_name="aaaAa", pop_keys=["object_data"])]
    , db_cursor)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["filter_text"] = "aA"
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == 4 # id = [100, 101, 102, 103]
    assert data["object_ids"] == [100, 101]
    delete_objects([100, 101, 102, 103], db_cursor)

    # Correct request - sort by object_name with no object names provided (query all object types)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["object_types"] = []
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == obj_count
    assert data["object_ids"] == [1, 2]

    # Correct request - sort by object_name and filter "link" object_type
    pi = deepcopy(pagination_info)
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [1, 2]

    # Correct request - sort by object_name and filter "markdown" object_type
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["object_types"] = ["markdown"]
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == markdown_count
    assert data["object_ids"] == [11, 12]

    # Correct request - filter objects by their tags (all object types)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["object_types"] = []
    pi["pagination_info"]["tags_filter"] = [1, 2, 3]
    resp = await cli.post("/objects/get_page_object_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert sorted(data["object_ids"]) == [5, 7]
    assert data["total_items"] == 4     # object_ids = [5, 7, 11, 12]


async def test_correct_requests_as_anonymous(cli, db_cursor):
    insert_data_for_view_objects_as_anonymous(cli, db_cursor)
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]

    # Get all objects on one page (and receive only published)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["items_per_page"] = 10
    resp = await cli.post("/objects/get_page_object_ids", json=pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(expected_object_ids)
    assert sorted(data["object_ids"]) == expected_object_ids
    

if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
