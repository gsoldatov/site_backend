"""
routes/objects.py tests
"""
import os
# import json
# from datetime import datetime
from copy import deepcopy

import pytest
# from psycopg2.extensions import AsIs

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
    
    # Incorrect link value
    link = deepcopy(test_link)
    link.pop("object_id")
    link["object_data"] = {"link": "not a valid URL"}
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400

    schema = config["db"]["db_schema"]  # Check that a new object was not created
    cursor.execute(f"SELECT object_name FROM {schema}.objects")
    assert not cursor.fetchone()
    cursor.execute(f"SELECT link FROM {schema}.url_links")
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
    cursor.execute(f"SELECT link FROM {schema}.url_links WHERE object_id = {resp_object['object_id']}")
    assert cursor.fetchone() == (link["object_data"]["link"],)

    # Check if an object existing name is not added
    link = deepcopy(test_link)
    link.pop("object_id")
    link["object_name"] = link["object_name"].upper()
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
