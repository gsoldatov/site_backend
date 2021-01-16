"""
routes/objects.py tests for general object operations.

Object tagging logic is tested in test_objects_tags.py
"""
import os
import json
from copy import deepcopy

import pytest
from psycopg2.extensions import AsIs

from util import check_ids
from fixtures.app import *
from fixtures.objects import *
from fixtures.tags import insert_tags, tag_list
from fixtures.objects_tags import insert_objects_tags


async def test_add(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    schema = config["db"]["db_schema"] 

    # Incorrect request body
    resp = await cli.post("/objects/add", data = "not a JSON document.")
    assert resp.status == 400
    
    # Required attributes missing
    for attr in ("object_type", "object_name", "object_description"):
        link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
        link.pop(attr)
        resp = await cli.post("/objects/add", json = {"object": link})
        assert resp.status == 400

    # Unallowed attributes
    link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
    link["unallowed"] = "unallowed"
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400

    # Incorrect values for general attributes
    for k, v in incorrect_object_values:
        if k != "object_id":
            link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
            link[k] = v
            resp = await cli.post("/objects/add", json = {"object": link})
            assert resp.status == 400

    # Add a correct object
    link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 200
    resp_json = await resp.json()
    assert "object" in resp_json
    resp_object = resp_json["object"]
    assert type(resp_object) == dict
    for attr in ("object_id", "object_type", "created_at", "modified_at", "object_name", "object_description"):
        assert attr in resp_object
    assert link["object_name"] == resp_object["object_name"]
    assert link["object_description"] == resp_object["object_description"]

    cursor.execute(f"SELECT object_name FROM {schema}.objects WHERE object_id = {resp_object['object_id']}")
    assert cursor.fetchone() == (link["object_name"],)

    # Check if an object with existing name is not added
    link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
    link["object_name"] = link["object_name"].upper()
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400


async def test_view(cli, db_cursor, config):
    # Insert mock values
    insert_objects(get_object_list(1, 10), db_cursor, config)
    insert_links(links_list, db_cursor, config)

    # Incorrect request body
    resp = await cli.post("/objects/view", data = "not a JSON document.")
    assert resp.status == 400

    for payload in [{}, {"object_ids": []}, {"object_ids": [1, -1]}, {"object_ids": [1, "abc"]},
                        {"object_data_ids": []}, {"object_data_ids": [1, -1]}, {"object_data_ids": [1, "abc"]},
                        {"object_ids": [1], "object_data_ids": [-1]}, {"object_ids": [-1], "object_data_ids": [1]}]:
        resp = await cli.post("/objects/view", json = payload)
        assert resp.status == 400

    # Non-existing ids
    for key in {"object_ids", "object_data_ids"}:
        resp = await cli.post("/objects/view", json = {key: [999, 1000]})
        assert resp.status == 404

    # Correct request (object_ids only)
    object_ids = [_ for _ in range(1, 11)]
    resp = await cli.post("/objects/view", json = {"object_ids": object_ids})
    assert resp.status == 200
    data = await resp.json()
    assert "objects" in data

    for field in ("object_id", "object_type", "object_name", "object_description", "created_at", "modified_at"):
        assert field in data["objects"][0]

    check_ids(object_ids, [data["objects"][x]["object_id"] for x in range(len(data["objects"]))], 
        "Objects view, correct request, object_ids only")
    
    # Correct request (object_data_ids only) is checked type-specific tests

    # Correct request (both types of data request)
    object_ids = [_ for _ in range(1, 6)]
    object_data_ids = [_ for _ in range(6, 11)]
    resp = await cli.post("/objects/view", json = {"object_ids": object_ids, "object_data_ids": object_data_ids})
    assert resp.status == 200
    data = await resp.json()
    for attr in ("objects", "object_data"):
        assert attr in data
    
    check_ids(object_ids, [data["objects"][x]["object_id"] for x in range(len(data["objects"]))], 
        "Objects view, correct request for both object attributes and data, object_ids")
    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request for both object attributes and data, object_data_ids")


async def test_update(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    objects = config["db"]["db_schema"] + ".objects"
    links = config["db"]["db_schema"] + ".links"

    # Insert mock values
    obj_list = [get_test_object(1, pop_keys = ["object_data"]), get_test_object(2, pop_keys = ["object_data"])]
    l_list = [get_test_object_data(1), get_test_object_data(2)]
    insert_objects(obj_list, db_cursor, config)
    insert_links(l_list, db_cursor, config)
    
    # Incorrect request body
    resp = await cli.put("/objects/update", data = "not a JSON document.")
    assert resp.status == 400

    for payload in ({}, {"test": "wrong attribute"}, {"object": "wrong value type"}):
        resp = await cli.put("/objects/update", json = payload)
        assert resp.status == 400
    
    # Missing attributes
    for attr in ("object_id", "object_name", "object_description"):
        obj = get_test_object(1, pop_keys = ["created_at", "modified_at", "object_type"])
        obj.pop(attr)
        resp = await cli.put("/objects/update", json = {"object": obj})
        assert resp.status == 400
    
    # Incorrect attribute types and lengths:
    for k, v in incorrect_object_values:
        if k != "object_type":
            obj = get_test_object(1, pop_keys = ["created_at", "modified_at", "object_type"])
            obj[k] = v
            resp = await cli.put("/objects/update", json = {"object": obj})
            assert resp.status == 400
    
    # Non-existing object_id
    obj = get_test_object(1, pop_keys = ["created_at", "modified_at", "object_type"])
    obj["object_id"] = 100
    resp = await cli.put("/objects/update", json = {"object": obj})
    assert resp.status == 404

    # Duplicate object_name
    obj = get_test_object(2, pop_keys = ["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json = {"object": obj})
    assert resp.status == 400

    # Lowercase duplicate object_name
    obj = get_test_object(2, pop_keys = ["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    obj["object_name"] = obj["object_name"].upper()
    resp = await cli.put("/objects/update", json = {"object": obj})
    assert resp.status == 400

    # Correct update (general attributes)
    obj = get_test_object(3, pop_keys = ["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json = {"object": obj})
    assert resp.status == 200
    cursor.execute(f"SELECT object_name FROM {objects} WHERE object_id = 1")
    assert cursor.fetchone() == (obj["object_name"],)

async def test_delete(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    objects = config["db"]["db_schema"] + ".objects"
    
    # Insert mock values
    obj_list = [get_test_object(1, pop_keys = ["object_data"]), get_test_object(2, pop_keys = ["object_data"]), get_test_object(3, pop_keys = ["object_data"])]
    l_list = [get_test_object_data(1), get_test_object_data(2), get_test_object_data(3)]
    insert_objects(obj_list, db_cursor, config)
    insert_links(l_list, db_cursor, config)
    
    # Incorrect attributes and values
    for value in ["123", {"incorrect_key": "incorrect_value"}, {"object_ids": "incorrect_value"}, {"object_ids": []}]:
        body = value if type(value) == str else json.dumps(value)
        resp = await cli.delete("/objects/delete", data = body)
        assert resp.status == 400
    
    # Non-existing object ids
    resp = await cli.delete("/objects/delete", json = {"object_ids": [1000, 2000]})
    assert resp.status == 404

    # Correct deletes (general data + link)
    resp = await cli.delete("/objects/delete", json = {"object_ids": [1]})
    assert resp.status == 200
    cursor.execute(f"SELECT object_id FROM {objects}")
    assert cursor.fetchone() == (2,)
    assert cursor.fetchone() == (3,)
    assert not cursor.fetchone()

    resp = await cli.delete("/objects/delete", json = {"object_ids": [2, 3]})
    assert resp.status == 200
    cursor.execute(f"SELECT object_id FROM {objects}")
    assert not cursor.fetchone()


async def test_get_page_object_ids(cli, db_cursor, config):
    pagination_info = {"pagination_info": {"page": 1, "items_per_page": 2, "order_by": "object_name", "sort_order": "asc", "filter_text": "", "object_types": ["link"], "tags_filter": []}}
    obj_list = get_object_list(1, 10)   # links
    obj_list.extend(get_object_list(11, 18)) # markdown
    obj_count = len(obj_list)
    links_count = sum((1 for obj in obj_list if obj["object_type"] == "link"))
    markdown_count = sum((1 for obj in obj_list if obj["object_type"] == "markdown"))

    # Insert mock values
    insert_objects(obj_list, db_cursor, config)

    insert_tags(tag_list, db_cursor, config, generate_tag_ids = True)
    objects_tags = {1: [1, 2, 3], 2: [3, 4, 5]}
    insert_objects_tags([_ for _ in range(1, 8)], [1], db_cursor, config)
    insert_objects_tags([_ for _ in range(5, 11)], [2], db_cursor, config)
    insert_objects_tags([1, 3, 5, 7, 9], [3], db_cursor, config)

    # Incorrect request body (not a json, missing attributes, wrong attributes)
    resp = await cli.post("/objects/get_page_object_ids", data = "not a JSON document.")
    assert resp.status == 400

    for attr in pagination_info["pagination_info"]:
        pi = deepcopy(pagination_info)
        pi["pagination_info"].pop(attr)
        resp = await cli.post("/objects/get_page_object_ids", json = pi)
        assert resp.status == 400

    # Incorrect param values
    for k, v in [("page", "text"), ("page", -1), ("items_per_page", "text"), ("items_per_page", -1), ("order_by", 1), ("order_by", "wrong text"),
                 ("sort_order", 1), ("sort_order", "wrong text"), ("filter_text", 1), ("object_types", "not a list"), ("object_types", ["wrong object type"]),
                 ("tags_filter", 1), ("tags_filter", "string"), ("tags_filter", [1, 2, -1]), ("tags_filter", [1, 2, "not a number"])]:
        pi = deepcopy(pagination_info)
        pi["pagination_info"][k] = v
        resp = await cli.post("/objects/get_page_object_ids", json = pi)
        assert resp.status == 400
    
    # Correct request - sort by object_name asc + check response body (links only)
    pi = deepcopy(pagination_info)
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
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
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [10, 9] # j1, h0

    # Correct request - sort by modified_at asc (links only)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["order_by"] = "modified_at"
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [8, 4]

    # Correct request - sort by modified_at desc + query second page (links only)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["page"] = 2
    pi["pagination_info"]["order_by"] = "modified_at"
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [7, 6]

    # Correct request - sort by object_name asc with filter text (links only)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["filter_text"] = "0"
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count // 2
    assert data["object_ids"] == [1, 3] # a0, c0

    # Correct request - sort by object_name with no object names provided (query all object types)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["object_types"] = []
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == obj_count
    assert data["object_ids"] == [1, 2]

    # Correct request - sort by object_name and filter "link" object_type
    pi = deepcopy(pagination_info)
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [1, 2]

    # Correct request - sort by object_name and filter "markdown" object_type
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["object_types"] = ["markdown"]
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == markdown_count
    assert data["object_ids"] == [11, 12]

    # Correct request - filter objects by their tags
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["tags_filter"] = [1, 2, 3]
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert sorted(data["object_ids"]) == [5, 7]


async def test_search(cli, db_cursor, config):
    # Insert mock values
    obj_list = get_object_list(1, 10)
    insert_objects(obj_list, db_cursor, config)

    # Incorrect request
    for req_body in ["not an object", 1, {"incorrect attribute": {}}, {"query": "not an object"}, {"query": 1},
        {"query": {"query_text": "123"}, "incorrect attribute": {}}, {"query": {"incorrect attribute": "123"}},
        {"query": {"query_text": "123", "incorrect_attribute": 1}}]:
        resp = await cli.post("/objects/search", json = req_body)
        assert resp.status == 400
    
    # Incorrect attribute values
    for req_body in [{"query": {"query_text": ""}}, {"query": {"query_text": 1}}, {"query": {"query_text": "a"*256}},
        {"query": {"query_text": "123", "maximum_values": "1"}}, {"query": {"query_text": "123", "maximum_values": -1}},
        {"query": {"query_text": "123", "maximum_values": 101}}]:
        resp = await cli.post("/objects/search", json = req_body)
        assert resp.status == 400
    
    # Correct request - non-existing objects
    req_body = {"query": {"query_text": "non-existing object"}}
    resp = await cli.post("/objects/search", json = req_body)
    assert resp.status == 404

    # Correct request - check response and maximum_values limit
    req_body = {"query": {"query_text": "0", "maximum_values": 2}}
    resp = await cli.post("/objects/search", json = req_body)
    assert resp.status == 200
    data = await resp.json()
    assert "object_ids" in data
    assert type(data["object_ids"]) == list
    assert data["object_ids"] == [1, 3]    # a0, c0

    # Correct request - check if query case is ignored
    insert_objects([{"object_id": 11, "object_type": "link", "created_at": obj_list[0]["created_at"], "modified_at": obj_list[0]["modified_at"], 
                    "object_name": "A", "object_description": ""}]
                    , db_cursor, config)
    req_body = {"query": {"query_text": "A"}}
    resp = await cli.post("/objects/search", json = req_body)
    assert resp.status == 200
    data = await resp.json()
    assert data["object_ids"] == [1, 11]    #a0, A

    req_body = {"query": {"query_text": "a"}}
    resp = await cli.post("/objects/search", json = req_body)
    assert resp.status == 200
    data = await resp.json()
    assert data["object_ids"] == [1, 11]    #a0, A

    # Correct request - check if existing_ids are excluded from result
    req_body = {"query": {"query_text": "0", "maximum_values": 2, "existing_ids": [1, 3, 9]}}
    resp = await cli.post("/objects/search", json = req_body)
    assert resp.status == 200
    data = await resp.json()
    assert data["object_ids"] == [5, 7]    #e0, g0


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
