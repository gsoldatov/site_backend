"""
routes/tags.py tests
"""
import os
import json
from datetime import datetime
from copy import deepcopy

import pytest
from psycopg2.extensions import AsIs

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
        resp = await cli.put("/tags/update", json = tag)
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


    """
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
    
    # Non-existing tag_id
    resp = await cli.delete("/tags/delete/asd")
    assert resp.status == 404

    resp = await cli.delete("/tags/delete/999999")
    assert resp.status == 404

    # Correct delete
    resp = await cli.delete("/tags/delete/1")
    assert resp.status == 200
    cursor.execute(f"SELECT tag_id FROM {table}")
    assert cursor.fetchone() == (2,)
    assert not cursor.fetchone()
    """
 

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
    resp = await cli.post("/tags/view", json = {"tag_ids": [_ for _ in range(1, 11)]})
    assert resp.status == 200
    data = await resp.json()
    assert "tags" in data

    expected_tag_ids = [_ for _ in range(1, 11)]
    for x in range(len(data["tags"])):
        try:
            expected_tag_ids.remove(data["tags"][x]["tag_id"])
        except KeyError:
            pytest.fail(f"tag_id = {x} not found in response body")
    assert len(expected_tag_ids) == 0
        
    for field in ("tag_id", "tag_name", "tag_description", "created_at", "modified_at"):
        assert field in data["tags"][0]


"""
# Old version with date/name sort and pagination support; replaced a route 
# which returns a list of tags by their ids
# Tests may fail because of tag_id generation change in tag_list fixture (0..9 -> 1..10)
async def test_view(cli, db_cursor, config):
    def get_response_tag_properties_as_list(response_json, prop = "tag_id"):
        return [response_json["tags"][x][prop] for x in range(len(response_json["tags"]))]
    
    tag_list_names_sorted_by_created_at = ["a", "e", "i", "b", "c", "d", "f", "g", "h", "j"]
    tag_list_names_sorted_by_created_at_desc = deepcopy(tag_list_names_sorted_by_created_at)
    tag_list_names_sorted_by_created_at_desc.reverse()
    
    # Insert data
    cursor = db_cursor(apply_migrations = True)
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s)" for _ in range(len(tag_list))))
    table = config["db"]["db_schema"] + ".tags"
    params = [AsIs(table)]
    for t in tag_list:
        params.extend(t.values())
    cursor.execute(query, params)

    # Check response structure and default param values
    resp = await cli.get("/tags/view")
    assert resp.status == 200
    data = await resp.json()
    for x in ("first", "last", "total", "tags"):    # response structure
        assert x in data
    assert data["first"] == 0
    assert data["last"] == 9
    assert data["total"] == 10

    for element in ("tag_id", "created_at", "modified_at", "tag_name", "tag_description"):     # response contains expected tag data
        assert element in data["tags"][0]
    tag_ids = [tag_list[x]["tag_id"] for x in range(len(tag_list))]
    resp_tag_ids = get_response_tag_properties_as_list(data)
    assert len(resp_tag_ids) == len(set(resp_tag_ids))
    assert sorted(tag_ids) == sorted(resp_tag_ids)

    # first & count params
    params = {"first": 3, "count": 3}
    resp = await cli.get("/tags/view", params = params)
    assert resp.status == 200
    data = await resp.json()
    assert data["first"] == 3
    assert data["last"] == 5
    assert data["total"] == 10
    assert get_response_tag_properties_as_list(data, "tag_name") == ["d", "e", "f"]

    # sort by tag_name asc
    params = {"order_by": "tag_name", "asc": "True"}
    resp = await cli.get("/tags/view", params = params)
    assert resp.status == 200
    data = await resp.json()
    assert get_response_tag_properties_as_list(data, "tag_name") == [chr(ord("a") + x) for x in range(10)]

    # sort by tag_name desc
    params = {"order_by": "tag_name", "asc": "False"}
    resp = await cli.get("/tags/view", params = params)
    assert resp.status == 200
    data = await resp.json()
    assert get_response_tag_properties_as_list(data, "tag_name") == [chr(ord("a") + 9 - x) for x in range(10)]

    # sort by created_at asc
    params = {"order_by": "created_at", "asc": "True"}
    resp = await cli.get("/tags/view", params = params)
    assert resp.status == 200
    data = await resp.json()
    assert get_response_tag_properties_as_list(data, "tag_name") == tag_list_names_sorted_by_created_at

    # sort by created_at desc
    params = {"order_by": "created_at", "asc": "False"}
    resp = await cli.get("/tags/view", params = params)
    assert resp.status == 200
    data = await resp.json()
    assert get_response_tag_properties_as_list(data, "tag_name") == tag_list_names_sorted_by_created_at_desc
"""


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
