"""
Tests for markdown-specific operations.
"""
import os
import json

import pytest
from psycopg2.extensions import AsIs

from util import check_ids
from fixtures.objects import *
from fixtures.users import headers_admin_token


async def test_add(cli, db_cursor, config):
    schema = config["db"]["db_schema"] 
    
    # Incorrect markdown attributes
    for attr in [{"incorrect MD attr": "123"}, {"incorrect MD attr": "123", "raw_text": "New text"}]:
        md = get_test_object(4, pop_keys=["object_id", "created_at", "modified_at"])
        md["object_data"] = attr
        resp = await cli.post("/objects/add", json={"object": md}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect markdown value
    md = get_test_object(4, pop_keys=["object_id", "created_at", "modified_at"])
    md["object_data"] = {"raw_text": ""}
    resp = await cli.post("/objects/add", json={"object": md}, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute(f"SELECT object_name FROM {schema}.objects") # Check that a new object was not created
    assert not db_cursor.fetchone()
    db_cursor.execute(f"SELECT raw_text FROM {schema}.markdown")
    assert not db_cursor.fetchone()

    # Add a correct markdown object
    md = get_test_object(4, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": md}, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert "object" in resp_json
    resp_object = resp_json["object"]

    db_cursor.execute(f"SELECT raw_text FROM {schema}.markdown WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (md["object_data"]["raw_text"],)


async def test_update(cli, db_cursor, config):
    objects = config["db"]["db_schema"] + ".objects"
    markdown = config["db"]["db_schema"] + ".markdown"

    # Insert mock values
    obj_list = [get_test_object(4, owner_id=1, pop_keys=["object_data"]), get_test_object(5, owner_id=1, pop_keys=["object_data"])]
    md_list = [get_test_object_data(4), get_test_object_data(5)]
    insert_objects(obj_list, db_cursor, config)
    insert_markdown(md_list, db_cursor, config)

    # Incorrect attributes in object_data for markdown
    for object_data in [{}, {"raw_text": "Some text", "incorrect_attr": 1}, {"link": ""}, {"link": 123}]:
        obj = get_test_object(6, pop_keys=["created_at", "modified_at", "object_type"])
        obj["object_id"] = 4
        obj["object_data"] = object_data
        resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 400

    # Correct update (markdown)
    obj = get_test_object(6, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 4
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT raw_text FROM {markdown} WHERE object_id = 4")
    assert db_cursor.fetchone() == (obj["object_data"]["raw_text"],)


async def test_view(cli, db_cursor, config):
    # Insert mock values
    insert_objects(get_objects_attributes_list(11, 20), db_cursor, config)
    insert_markdown(markdown_data_list, db_cursor, config)

    # Correct request (object_data_ids only, links), non-existing ids
    object_data_ids = [_ for _ in range(1001, 1011)]
    resp = await cli.post("/objects/view", json={"object_data_ids": object_data_ids}, headers=headers_admin_token)
    assert resp.status == 404
    
    # Correct request (object_data_ids only, markdown)
    object_data_ids = [_ for _ in range(11, 21)]
    resp = await cli.post("/objects/view", json={"object_data_ids": object_data_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "object_data" in data

    for field in ("object_id", "object_type", "object_data"):
        assert field in data["object_data"][0]
    assert "raw_text" in data["object_data"][0]["object_data"]

    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request, markdown object_data_ids only")


async def test_delete(cli, db_cursor, config):
    markdown = config["db"]["db_schema"] + ".markdown"
    
    # Insert mock values
    obj_list = [get_test_object(4, owner_id=1, pop_keys=["object_data"]), 
        get_test_object(5, owner_id=1, pop_keys=["object_data"]), get_test_object(6, owner_id=1, pop_keys=["object_data"])]
    md_list = [get_test_object_data(4), get_test_object_data(5), get_test_object_data(6)]
    insert_objects(obj_list, db_cursor, config)
    insert_markdown(md_list, db_cursor, config)

    # Correct deletes (general data + link)
    resp = await cli.delete("/objects/delete", json={"object_ids": [4]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM {markdown}")
    assert db_cursor.fetchone() == (5,)
    assert db_cursor.fetchone() == (6,)
    assert not db_cursor.fetchone()

    resp = await cli.delete("/objects/delete", json={"object_ids": [5, 6]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM {markdown}")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
