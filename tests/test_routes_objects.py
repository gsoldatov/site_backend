"""
routes/objects.py tests
"""
import os
# import json
# from datetime import datetime
from copy import deepcopy

import pytest
from psycopg2.extensions import AsIs

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
    link["object_data"] = {"link": "not a valid URL"}
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400

    schema = config["db"]["db_schema"]  # Check that a new object was not created
    cursor.execute(f"SELECT object_name FROM {schema}.objects")
    assert not cursor.fetchone()
    cursor.execute(f"SELECT link FROM {schema}.urls")
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
    cursor.execute(f"SELECT link FROM {schema}.urls WHERE object_id = {resp_object['object_id']}")
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
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s)" for _ in range(len(objects_list))))
    table = config["db"]["db_schema"] + ".objects"
    params = [AsIs(table)]
    for t in objects_list:
        params.extend(t.values())
    cursor.execute(query, params)

    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(urls_list))))
    table = config["db"]["db_schema"] + ".urls"
    params = [AsIs(table)]
    for t in urls_list:
        params.extend(t.values())
    cursor.execute(query, params)

    # Incorrect request body
    resp = await cli.post("/objects/view", data = "not a JSON document.")
    assert resp.status == 400

    for payload in [{}, {"object_ids": []}, {"object_ids": [1, -1]}, {"object_ids": [1, "abc"]}]:
        resp = await cli.post("/objects/view", json = payload)
        assert resp.status == 400

    # Non-existing ids
    resp = await cli.post("/objects/view", json = {"object_ids": [999, 1000]})
    assert resp.status == 404

    # Correct request
    resp = await cli.post("/objects/view", json = {"object_ids": [_ for _ in range(1, 11)]})
    assert resp.status == 200
    data = await resp.json()
    assert "objects" in data

    expected_object_ids = [_ for _ in range(1, 11)]
    for x in range(len(data["objects"])):
        try:
            expected_object_ids.remove(data["objects"][x]["object_id"])
        except KeyError:
            pytest.fail(f"object_id = {x} not found in response body")
    assert len(expected_object_ids) == 0
        
    for field in ("object_id", "object_type", "object_name", "object_description", "created_at", "modified_at", "object_data"):
        assert field in data["objects"][0]
    
    assert "link" in data["objects"][0]["object_data"]


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
