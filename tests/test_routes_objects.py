"""
routes/objects.py tests
"""
import os
import json
from datetime import datetime
from copy import deepcopy

import pytest
from psycopg2.extensions import AsIs

from util import check_ids
from fixtures_app import *
from fixtures_objects import *


async def test_add(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)

    # Incorrect request body
    resp = await cli.post("/objects/add", data = "not a JSON document.")
    assert resp.status == 400
    
    # Required attributes missing
    for attr in ("object_type", "object_name", "object_description"):
        link = deepcopy(test_link)
        link.pop("object_id")
        link.pop(attr)
        resp = await cli.post("/objects/add", json = {"object": link})
        assert resp.status == 400

    # Unallowed attributes
    link = deepcopy(test_link)
    link.pop("object_id")
    link["unallowed"] = "unallowed"
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400

    # Incorrect values for general attribute
    for k, v in incorrect_object_values:
        if k != "object_id":
            link = deepcopy(test_link)
            link.pop("object_id")
            link[k] = v
            resp = await cli.post("/objects/add", json = {"object": link})
            assert resp.status == 400
    
    # Incorrect link attributes
    for attrs in [{"incorrect link attr": "123"}, {"incorrect link attr": "123", "link": "https://google.com"}]:
        link = deepcopy(test_link)
        link["object_data"] = attr
        resp = await cli.post("/objects/add", json = {"object": link})
        assert resp.status == 400
    
    # Incorrect link value
    link = deepcopy(test_link)
    link.pop("object_id")
    link["object_data"] = {"link": "not a valid link"}
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400

    schema = config["db"]["db_schema"]  # Check that a new object was not created
    cursor.execute(f"SELECT object_name FROM {schema}.objects")
    assert not cursor.fetchone()
    cursor.execute(f"SELECT link FROM {schema}.links")
    assert not cursor.fetchone()

    # Add a correct link
    link = deepcopy(test_link)
    link.pop("object_id")
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
    cursor.execute(f"SELECT link FROM {schema}.links WHERE object_id = {resp_object['object_id']}")
    assert cursor.fetchone() == (link["object_data"]["link"],)

    # Check if an object existing name is not added
    link = deepcopy(test_link)
    link.pop("object_id")
    link["object_name"] = link["object_name"].upper()
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400


async def test_view(cli, db_cursor, config):
    # Insert data
    cursor = db_cursor(apply_migrations = True)
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s)" for _ in range(len(object_list))))
    table = config["db"]["db_schema"] + ".objects"
    params = [AsIs(table)]
    for t in object_list:
        params.extend(t.values())
    cursor.execute(query, params)

    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(links_list))))
    table = config["db"]["db_schema"] + ".links"
    params = [AsIs(table)]
    for t in links_list:
        params.extend(t.values())
    cursor.execute(query, params)

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
    
    # Correct request (object_ids only, links)
    object_data_ids = [_ for _ in range(1, 11)]
    resp = await cli.post("/objects/view", json = {"object_data_ids": object_data_ids})
    assert resp.status == 200
    data = await resp.json()
    assert "object_data" in data

    for field in ("object_id", "object_type", "object_data"):
        assert field in data["object_data"][0]
    assert "link" in data["object_data"][0]["object_data"]

    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request, object_data_ids only")

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
    created_at = datetime.utcnow()
    modified_at = created_at

    # Insert mock values
    cursor.execute("INSERT INTO %s VALUES (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s)",
                (AsIs(objects), 
                test_link["object_id"], test_link["object_type"], created_at, modified_at, test_link["object_name"], test_link["object_description"],
                test_link2["object_id"], test_link2["object_type"], created_at, modified_at, test_link2["object_name"], test_link2["object_description"])
                )
    
    cursor.execute("INSERT INTO %s VALUES (%s, %s), (%s, %s)",
                (AsIs(links), 
                test_link["object_id"], test_link["object_data"]["link"],
                test_link2["object_id"], test_link2["object_data"]["link"])
                )
    
    # Incorrect request body
    resp = await cli.put("/objects/update", data = "not a JSON document.")
    assert resp.status == 400

    for payload in ({}, {"test": "wrong attribute"}, {"object": "wrong value type"}):
        resp = await cli.put("/objects/update", json = payload)
        assert resp.status == 400
    
    # Missing attributes
    for attr in ("object_id", "object_name", "object_description"):
        obj = deepcopy(test_link)
        obj.pop("object_type")
        obj.pop(attr)
        resp = await cli.put("/objects/update", json = {"object": obj})
        assert resp.status == 400
    
    # Incorrect attribute types and lengths:
    for k, v in incorrect_object_values:
        if k != "object_type":
            obj = deepcopy(test_link)
            obj.pop("object_type")
            obj[k] = v
            resp = await cli.put("/objects/update", json = {"object": obj})
            assert resp.status == 400
    
    # Non-existing object_id
    obj = deepcopy(test_link)
    obj.pop("object_type")
    obj["object_id"] = 100
    resp = await cli.put("/objects/update", json = {"object": obj})
    assert resp.status == 404

    # Duplicate object_name
    obj = deepcopy(test_link2)
    obj.pop("object_type")
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json = {"object": obj})
    assert resp.status == 400

    # Lowercase duplicate object_name
    obj = deepcopy(test_link2)
    obj.pop("object_type")
    obj["object_id"] = 1
    obj["object_name"] = obj["object_name"].upper()
    resp = await cli.put("/objects/update", json = {"object": obj})
    assert resp.status == 400

    # Incorrect attributes in object_data for links
    for object_data in [{}, {"link": "https://google.com", "incorrect_attr": 1}, {"link": "not a link"},
                        {"link": ""}, {"link": 123}]:
        obj = deepcopy(test_link2)
        obj.pop("object_type")
        obj["object_id"] = 1
        obj["object_data"] = object_data
        resp = await cli.put("/objects/update", json = {"object": obj})
        assert resp.status == 400

    # Correct update (general attributes + link)
    obj = deepcopy(test_link3)
    obj.pop("object_type")
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json = {"object": obj})
    assert resp.status == 200
    cursor.execute(f"SELECT object_name FROM {objects} WHERE object_id = 1")
    assert cursor.fetchone() == (obj["object_name"],)
    cursor.execute(f"SELECT link FROM {links} WHERE object_id = 1")
    assert cursor.fetchone() == (obj["object_data"]["link"],)


async def test_delete(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    objects = config["db"]["db_schema"] + ".objects"
    links = config["db"]["db_schema"] + ".links"
    created_at = datetime.utcnow()
    modified_at = created_at

    # Insert mock values
    cursor.execute("INSERT INTO %s VALUES (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s)",
                (AsIs(objects), 
                test_link["object_id"], test_link["object_type"], created_at, modified_at, test_link["object_name"], test_link["object_description"],
                test_link2["object_id"], test_link2["object_type"], created_at, modified_at, test_link2["object_name"], test_link2["object_description"],
                test_link3["object_id"], test_link3["object_type"], created_at, modified_at, test_link3["object_name"], test_link3["object_description"])
                )
    
    cursor.execute("INSERT INTO %s VALUES (%s, %s), (%s, %s), (%s, %s)",
                (AsIs(links), 
                test_link["object_id"], test_link["object_data"]["link"],
                test_link2["object_id"], test_link2["object_data"]["link"],
                test_link3["object_id"], test_link3["object_data"]["link"])
                )
    
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
    for table in [objects, links]:
        cursor.execute(f"SELECT object_id FROM {table}")
        assert cursor.fetchone() == (2,)
        assert cursor.fetchone() == (3,)
        assert not cursor.fetchone()

    resp = await cli.delete("/objects/delete", json = {"object_ids": [2, 3]})
    assert resp.status == 200
    for table in [objects, links]:
        cursor.execute(f"SELECT object_id FROM {table}")
        assert not cursor.fetchone()


async def test_get_page_object_ids(cli, db_cursor, config):
    pagination_info = {"pagination_info": {"page": 1, "items_per_page": 2, "order_by": "object_name", "sort_order": "asc", "filter_text": "", "object_types": ["link"]}}
    links_count = sum((1 for obj in object_list if obj["object_type"] == "link")) # TODO change total count in subtests and default object types when new types are added

    # Insert data
    cursor = db_cursor(apply_migrations = True)
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s)" for _ in range(len(object_list))))
    table = config["db"]["db_schema"] + ".objects"
    params = [AsIs(table)]
    for t in object_list:
        params.extend(t.values())
    cursor.execute(query, params)

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
                 ("sort_order", 1), ("sort_order", "wrong text"), ("filter_text", 1), ("object_types", "not a list"), ("object_types", ["wrong object type"])]:
        pi = deepcopy(pagination_info)
        pi["pagination_info"][k] = v
        resp = await cli.post("/objects/get_page_object_ids", json = pi)
        assert resp.status == 400
    
    # Correct request - sort by object_name asc + check response body
    pi = deepcopy(pagination_info)
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    for attr in ["page", "items_per_page","total_items", "order_by", "sort_order", "filter_text", "object_types", "object_ids"]:
        assert attr in data
        assert data[attr] == pi["pagination_info"].get(attr, None) or attr in ["object_types", "total_items", "object_ids"]
    assert data["total_items"] == links_count
    assert data["object_ids"] == [1, 2] # a0, b1

    # Correct request - sort by object_name desc
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [10, 9] # j1, h0

    # Correct request - sort by modified_at asc
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["order_by"] = "modified_at"
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [8, 4]

    # Correct request - sort by modified_at desc + query second page
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["page"] = 2
    pi["pagination_info"]["order_by"] = "modified_at"
    pi["pagination_info"]["sort_order"] = "desc"
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [7, 6]

    # Correct request - sort by object_name asc with filter text
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
    assert data["total_items"] == links_count
    assert data["object_ids"] == [1, 2]

    # Correct request - sort by object_name and filter "link" object_type
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["object_types"] = []
    resp = await cli.post("/objects/get_page_object_ids", json = pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["total_items"] == links_count
    assert data["object_ids"] == [1, 2]


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
