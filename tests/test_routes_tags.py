"""
routes/tags.py tests
"""
import os
import json
from datetime import datetime
from copy import deepcopy

import pytest
from psycopg2.extensions import AsIs

from util import check_ids
from fixtures_app import *
from fixtures_tags import *


async def test_add(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)

    # Incorrect request body
    resp = await cli.post("/tags/add", data = "not a JSON document.")
    assert resp.status == 400

    # Check required elements
    for attr in ("tag_name", "tag_description"):
        tag = deepcopy(test_tag)
        tag.pop("tag_id")
        tag.pop(attr)
        resp = await cli.post("/tags/add", json = {"tag": tag})
        assert resp.status == 400

    # Unallowed elements
    tag = deepcopy(test_tag)
    tag.pop("tag_id")
    tag["unallowed"] = "unallowed"
    resp = await cli.post("/tags/add", json = {"tag": tag})
    assert resp.status == 400

    # Incorrect values
    for k, v in incorrect_tag_values:
        if k != "tag_id":
            tag = deepcopy(test_tag)
            tag.pop("tag_id")
            tag[k] = v
            resp = await cli.post("/tags/add", json = {"tag": tag})
            assert resp.status == 400

    # Write a correct tag
    tag = deepcopy(test_tag)
    tag.pop("tag_id")
    resp = await cli.post("/tags/add", json = {"tag": tag})
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
    cursor.execute(f"SELECT tag_name FROM {schema}.tags WHERE tag_id = 1")
    assert cursor.fetchone() == (tag["tag_name"],)

    # Add an existing tag_name
    resp = await cli.post("/tags/add", json = {"tag": tag})
    assert resp.status == 400


async def test_update(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    table = config["db"]["db_schema"] + ".tags"
    created_at = datetime.utcnow()
    modified_at = created_at

    # Insert mock values
    cursor.execute("INSERT INTO %s VALUES (1, %s, %s, %s, %s), (2, %s, %s, %s, %s)",
                (AsIs(table), 
                created_at, modified_at, test_tag["tag_name"], test_tag["tag_description"],
                created_at, modified_at, test_tag2["tag_name"], test_tag2["tag_description"])
                )
    
    # Incorrect request body
    resp = await cli.put("/tags/update", data = "not a JSON document.")
    assert resp.status == 400

    for payload in ({}, {"test": "wrong attribute"}, {"tag": "wrong value type"}):
        resp = await cli.put("/tags/update", json = payload)
        assert resp.status == 400
    
    # Missing attributes
    for attr in ("tag_id", "tag_name", "tag_description"):
        tag = deepcopy(test_tag)
        tag.pop(attr)
        resp = await cli.put("/tags/update", json = {"tag": tag})
        assert resp.status == 400
    
    # Incorrect attribute types and lengths:
    for k, v in incorrect_tag_values:
        tag = deepcopy(test_tag)
        tag[k] = v
        resp = await cli.put("/tags/update", json = {"tag": tag})
        assert resp.status == 400
    
    # Non-existing tag_id
    tag = deepcopy(test_tag)
    tag["tag_id"] = 100
    resp = await cli.put("/tags/update", json = {"tag": tag})
    assert resp.status == 404

    # Duplicate tag_name
    tag = deepcopy(test_tag2)
    tag["tag_id"] = 1
    resp = await cli.put("/tags/update", json = {"tag": tag})
    assert resp.status == 400
    
    # Lowercase duplicate tag_name
    tag = deepcopy(test_tag2)
    tag["tag_id"] = 1
    tag["tag_name"] = tag["tag_name"].upper()
    resp = await cli.put("/tags/update", json = {"tag": tag})
    assert resp.status == 400
    
    # Correct update
    tag = deepcopy(test_tag3)
    tag["tag_id"] = 1
    resp = await cli.put("/tags/update", json = {"tag": tag})
    assert resp.status == 200
    cursor.execute(f"SELECT tag_name FROM {table} WHERE tag_id = 1")
    assert cursor.fetchone() == (tag["tag_name"],)


async def test_delete(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    table = config["db"]["db_schema"] + ".tags"
    created_at = datetime.utcnow()
    modified_at = created_at

    # Insert mock values
    cursor.execute("INSERT INTO %s VALUES (1, %s, %s, %s, %s), (2, %s, %s, %s, %s), (3, %s, %s, %s, %s)", 
        (AsIs(table), 
        created_at, modified_at, test_tag["tag_name"], test_tag["tag_description"],
        created_at, modified_at, test_tag2["tag_name"], test_tag2["tag_description"],
        created_at, modified_at, test_tag3["tag_name"], test_tag3["tag_description"])
    )
    
    # Incorrect values
    for value in ["123", {"incorrect_key": "incorrect_value"}, {"tag_ids": "incorrect_value"}, {"tag_ids": []}]:
        body = value if type(value) == str else json.dumps(value)
        resp = await cli.delete("/tags/delete", data = body)
        assert resp.status == 400
    
    # Non-existing tag_id
    resp = await cli.delete("/tags/delete", json = {"tag_ids": [1000, 2000]})
    assert resp.status == 404

    # Correct deletes
    resp = await cli.delete("/tags/delete", json = {"tag_ids": [1]})
    assert resp.status == 200
    cursor.execute(f"SELECT tag_id FROM {table}")
    assert cursor.fetchone() == (2,)
    assert cursor.fetchone() == (3,)
    assert not cursor.fetchone()

    resp = await cli.delete("/tags/delete", json = {"tag_ids": [2, 3]})
    assert resp.status == 200
    cursor.execute(f"SELECT tag_id FROM {table}")
    assert not cursor.fetchone()
 

async def test_view(cli, db_cursor, config):
    # Insert data
    cursor = db_cursor(apply_migrations = True)
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s)" for _ in range(len(tag_list))))
    table = config["db"]["db_schema"] + ".tags"
    params = [AsIs(table)]
    for t in tag_list:
        params.extend(t.values())
    cursor.execute(query, params)

    # Incorrect request body
    resp = await cli.post("/tags/view", data = "not a JSON document.")
    assert resp.status == 400
    
    for payload in [{}, {"tag_ids": []}, {"tag_ids": [1, -1]}, {"tag_ids": [1, "abc"]}]:
        resp = await cli.post("/tags/view", json = payload)
        assert resp.status == 400
    
    # Non-existing ids
    resp = await cli.post("/tags/view", json = {"tag_ids": [999, 1000]})
    assert resp.status == 404

    # Correct request
    tag_ids = [_ for _ in range(1, 11)]
    resp = await cli.post("/tags/view", json = {"tag_ids": tag_ids})
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

    cursor = db_cursor(apply_migrations = True)
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s)" for _ in range(len(tag_list))))
    table = config["db"]["db_schema"] + ".tags"
    params = [AsIs(table)]
    for t in tag_list:
        params.extend(t.values())
    cursor.execute(query, params)

    # Incorrect request body
    resp = await cli.post("/tags/get_page_tag_ids", data = "not a JSON document.")
    assert resp.status == 400

    for attr in pagination_info["pagination_info"]:
        pi = deepcopy(pagination_info)
        pi["pagination_info"].pop(attr)
        resp = await cli.post("/tags/get_page_tag_ids", json = pi)
        assert resp.status == 400
    
    # Incorrect param values
    for k, v in [("page", "text"), ("page", -1), ("items_per_page", "text"), ("items_per_page", -1), ("order_by", 1), ("order_by", "wrong text"),
                 ("sort_order", 1), ("sort_order", "wrong text"), ("filter_text", 1)]:
        pi = deepcopy(pagination_info)
        pi["pagination_info"][k] = v
        resp = await cli.post("/tags/get_page_tag_ids", json = pi)
        assert resp.status == 400
    
    # Correct request - sort by tag_name asc + response body
    pi = deepcopy(pagination_info)
    resp = await cli.post("/tags/get_page_tag_ids", json = pi)
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
    resp = await cli.post("/tags/get_page_tag_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [10, 9] # j1, h0

    # Correct request - sort by modified_at asc
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["order_by"] = "modified_at"
    resp = await cli.post("/tags/get_page_tag_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [1, 5] # a0, e0

    # Correct request - sort by modified_at desc + second page
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["page"] = 2
    pi["pagination_info"]["order_by"] = "modified_at"
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/tags/get_page_tag_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list)
    assert data["tag_ids"] == [7, 6] # g0, f1

    # Correct request - sort by tag_name asc with filter text
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["filter_text"] = "0"
    resp = await cli.post("/tags/get_page_tag_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == len(tag_list) // 2
    assert data["tag_ids"] == [1, 3] # a0, c0


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
