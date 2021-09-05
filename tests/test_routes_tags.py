"""
routes/tags.py tests.

Object tagging logic is tested in test_objects_tags.py
"""
import os
import json
from copy import deepcopy

import pytest

from util import check_ids
from fixtures.tags import *
from fixtures.users import headers_admin_token


async def test_add(cli, db_cursor, config):
    # Incorrect request body
    resp = await cli.post("/tags/add", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Check required elements
    for attr in ("tag_name", "tag_description"):
        tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
        tag.pop(attr)
        resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 400

    # Unallowed elements
    tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
    tag["unallowed"] = "unallowed"
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    for k, v in incorrect_tag_values:
        if k != "tag_id":
            tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
            tag[k] = v
            resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
            assert resp.status == 400

    # Write a correct tag
    tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert "tag" in resp_json
    resp_tag = resp_json["tag"]
    assert type(resp_tag) == dict
    assert "tag_id" in resp_tag
    assert "created_at" in resp_tag
    assert "modified_at" in resp_tag
    assert tag["tag_name"] == resp_tag["tag_name"]
    assert tag["tag_description"] == resp_tag["tag_description"]

    schema = config["db"]["db_schema"]
    db_cursor.execute(f"SELECT tag_name FROM {schema}.tags WHERE tag_id = 1")
    assert db_cursor.fetchone() == (tag["tag_name"],)

    # Add an existing tag_name
    resp = await cli.post("/tags/add", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400


async def test_update(cli, db_cursor, config):
    table = config["db"]["db_schema"] + ".tags"
    
    # Insert mock values
    tag_list = [get_test_tag(1), get_test_tag(2)]
    insert_tags(tag_list, db_cursor, config)
    
    # Incorrect request body
    resp = await cli.put("/tags/update", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for payload in ({}, {"test": "wrong attribute"}, {"tag": "wrong value type"}):
        resp = await cli.put("/tags/update", json=payload, headers=headers_admin_token)
        assert resp.status == 400
    
    # Missing attributes
    for attr in ("tag_id", "tag_name", "tag_description"):
        tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
        tag.pop(attr)
        resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute types and lengths:
    for k, v in incorrect_tag_values:
        tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
        tag[k] = v
        resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Non-existing tag_id
    tag = get_test_tag(1, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 100
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 404

    # Duplicate tag_name
    tag = get_test_tag(2, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 1
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400
    
    # Lowercase duplicate tag_name
    tag = get_test_tag(2, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 1
    tag["tag_name"] = tag["tag_name"].upper()
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 400
    
    # Correct update
    tag = get_test_tag(3, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 1
    resp = await cli.put("/tags/update", json={"tag": tag}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT tag_name FROM {table} WHERE tag_id = 1")
    assert db_cursor.fetchone() == (tag["tag_name"],)


async def test_delete(cli, db_cursor, config):
    table = config["db"]["db_schema"] + ".tags"

    # Insert mock values
    tag_list = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
    insert_tags(tag_list, db_cursor, config)
    
    # Incorrect values
    for value in ["123", {"incorrect_key": "incorrect_value"}, {"tag_ids": "incorrect_value"}, {"tag_ids": []}]:
        body = value if type(value) == str else json.dumps(value)
        resp = await cli.delete("/tags/delete", data=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Non-existing tag_id
    resp = await cli.delete("/tags/delete", json={"tag_ids": [1000, 2000]}, headers=headers_admin_token)
    assert resp.status == 404

    # Correct deletes
    resp = await cli.delete("/tags/delete", json={"tag_ids": [1]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT tag_id FROM {table}")
    assert db_cursor.fetchone() == (2,)
    assert db_cursor.fetchone() == (3,)
    assert not db_cursor.fetchone()

    resp = await cli.delete("/tags/delete", json={"tag_ids": [2, 3]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT tag_id FROM {table}")
    assert not db_cursor.fetchone()
 

async def test_view(cli, db_cursor, config):
    # Insert data
    insert_tags(tag_list, db_cursor, config)

    # Incorrect request body
    resp = await cli.post("/tags/view", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400
    
    for payload in [{}, {"tag_ids": []}, {"tag_ids": [1, -1]}, {"tag_ids": [1, "abc"]}]:
        resp = await cli.post("/tags/view", json=payload, headers=headers_admin_token)
        assert resp.status == 400
    
    # Non-existing ids
    resp = await cli.post("/tags/view", json={"tag_ids": [999, 1000]}, headers=headers_admin_token)
    assert resp.status == 404

    # Correct request
    tag_ids = [_ for _ in range(1, 11)]
    resp = await cli.post("/tags/view", json={"tag_ids": tag_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "tags" in data

    check_ids(tag_ids, [data["tags"][x]["tag_id"] for x in range(len(data["tags"]))], 
        "Tags view, correct request")
        
    for field in ("tag_id", "tag_name", "tag_description", "created_at", "modified_at"):
        assert field in data["tags"][0]


async def test_get_page_tag_ids(cli, db_cursor, config):
    # Insert data
    pagination_info = {"pagination_info": {"page": 1, "items_per_page": 2, "order_by": "tag_name", "sort_order": "asc", "filter_text": ""}}
    insert_tags(tag_list, db_cursor, config)

    # Incorrect request body
    resp = await cli.post("/tags/get_page_tag_ids", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for attr in pagination_info["pagination_info"]:
        pi = deepcopy(pagination_info)
        pi["pagination_info"].pop(attr)
        resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect param values
    for k, v in [("page", "text"), ("page", -1), ("items_per_page", "text"), ("items_per_page", -1), ("order_by", 1), ("order_by", "wrong text"),
                 ("sort_order", 1), ("sort_order", "wrong text"), ("filter_text", 1)]:
        pi = deepcopy(pagination_info)
        pi["pagination_info"][k] = v
        resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
        assert resp.status == 400
    
    # Correct request - sort by tag_name asc + response body
    pi = deepcopy(pagination_info)
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
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
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [10, 9] # j1, h0

    # Correct request - sort by modified_at asc
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["order_by"] = "modified_at"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [1, 5] # a0, e0

    # Correct request - sort by modified_at desc + second page
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["page"] = 2
    pi["pagination_info"]["order_by"] = "modified_at"
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [7, 6] # g0, f1

    # Correct request - sort by tag_name asc with filter text
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["filter_text"] = "0"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list) // 2
    assert data["tag_ids"] == [1, 3] # a0, c0

    # Correct request - filter by text + check if filter_text case is ignored
    insert_tags([get_test_tag(100, "aa"), get_test_tag(101, "AaA"), get_test_tag(102, "AAaa"), get_test_tag(103, "aaaAa")], db_cursor, config)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["filter_text"] = "aA"
    resp = await cli.post("/tags/get_page_tag_ids", json=pi, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == 4 # id = [100, 101, 102, 103]
    assert data["tag_ids"] == [100, 101]
    delete_tags([100, 101, 102, 103], db_cursor, config)


async def test_search(cli, db_cursor, config):
    # Insert data
    insert_tags(tag_list, db_cursor, config)

    # Incorrect request
    for req_body in ["not an object", 1, {"incorrect attribute": {}}, {"query": "not an object"}, {"query": 1},
        {"query": {"query_text": "123"}, "incorrect attribute": {}}, {"query": {"incorrect attribute": "123"}},
        {"query": {"query_text": "123", "incorrect_attribute": 1}}]:
        resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute values
    for req_body in [{"query": {"query_text": ""}}, {"query": {"query_text": 1}}, {"query": {"query_text": "a"*256}},
        {"query": {"query_text": "123", "maximum_values": "1"}}, {"query": {"query_text": "123", "maximum_values": -1}},
        {"query": {"query_text": "123", "maximum_values": 101}}]:
        resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Correct request - non-existing tags
    req_body = {"query": {"query_text": "non-existing tag"}}
    resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 404

    # Correct request - check response and maximum_values limit
    req_body = {"query": {"query_text": "0", "maximum_values": 2}}
    resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "tag_ids" in data
    assert type(data["tag_ids"]) == list
    assert data["tag_ids"] == [1, 3]    # a0, c0

    # Correct request - check if query case is ignored
    insert_tags([{"tag_id": 11, "created_at": tag_list[0]["created_at"], "modified_at": tag_list[0]["modified_at"], 
                    "tag_name": "A", "tag_description": ""}]
                    , db_cursor, config)
    req_body = {"query": {"query_text": "A"}}
    resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [1, 11]    #a0, A

    req_body = {"query": {"query_text": "a"}}
    resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [1, 11]    #a0, A

    # Correct request - check if existing_ids are excluded from result
    req_body = {"query": {"query_text": "0", "maximum_values": 2, "existing_ids": [1, 3, 9]}}
    resp = await cli.post("/tags/search", json=req_body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert data["tag_ids"] == [5, 7]    #e0, g0


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
