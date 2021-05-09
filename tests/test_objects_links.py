"""
Tests for link-specific operations.
"""
import os
import json

import pytest
from psycopg2.extensions import AsIs

from util import check_ids
from fixtures.objects import *


async def test_add(cli, db_cursor, config):
    schema = config["db"]["db_schema"] 
    
    # Incorrect link attributes
    for attr in [{"incorrect link attr": "123"}, {"incorrect link attr": "123", "link": "https://google.com"}]:
        link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
        link["object_data"] = attr
        resp = await cli.post("/objects/add", json = {"object": link})
        assert resp.status == 400
    
    # Incorrect link value
    link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
    link["object_data"] = {"link": "not a valid link"}
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400

    db_cursor.execute(f"SELECT object_name FROM {schema}.objects") # Check that a new object was not created
    assert not db_cursor.fetchone()
    db_cursor.execute(f"SELECT link FROM {schema}.links")
    assert not db_cursor.fetchone()

    # Add a correct link
    link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 200
    resp_json = await resp.json()
    assert "object" in resp_json
    resp_object = resp_json["object"]

    db_cursor.execute(f"SELECT link FROM {schema}.links WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (link["object_data"]["link"],)


async def test_update(cli, db_cursor, config):
    objects = config["db"]["db_schema"] + ".objects"
    links = config["db"]["db_schema"] + ".links"

    # Insert mock values
    obj_list = [get_test_object(1, pop_keys = ["object_data"]), get_test_object(2, pop_keys = ["object_data"])]
    l_list = [get_test_object_data(1), get_test_object_data(2)]
    insert_objects(obj_list, db_cursor, config)
    insert_links(l_list, db_cursor, config)

    # Incorrect attributes in object_data for links
    for object_data in [{}, {"link": "https://google.com", "incorrect_attr": 1}, {"link": "not a link"},
                        {"link": ""}, {"link": 123}]:
        obj = get_test_object(3, pop_keys = ["created_at", "modified_at", "object_type"])
        obj["object_id"] = 1
        obj["object_data"] = object_data
        resp = await cli.put("/objects/update", json = {"object": obj})
        assert resp.status == 400

    # Correct update (link)
    obj = get_test_object(3, pop_keys = ["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json = {"object": obj})
    assert resp.status == 200
    db_cursor.execute(f"SELECT link FROM {links} WHERE object_id = 1")
    assert db_cursor.fetchone() == (obj["object_data"]["link"],)


async def test_view(cli, db_cursor, config):
    # Insert mock values
    insert_objects(get_objects_attributes_list(1, 10), db_cursor, config)
    insert_links(links_data_list, db_cursor, config)

    # Correct request (object_data_ids only, links), non-existing ids
    object_data_ids = [_ for _ in range(1001, 1011)]
    resp = await cli.post("/objects/view", json = {"object_data_ids": object_data_ids})
    assert resp.status == 404
    
    # Correct request (object_data_ids only, links)
    object_data_ids = [_ for _ in range(1, 11)]
    resp = await cli.post("/objects/view", json = {"object_data_ids": object_data_ids})
    assert resp.status == 200
    data = await resp.json()
    assert "object_data" in data

    for field in ("object_id", "object_type", "object_data"):
        assert field in data["object_data"][0]
    assert "link" in data["object_data"][0]["object_data"]

    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request, link object_data_ids only")


async def test_delete(cli, db_cursor, config):
    links = config["db"]["db_schema"] + ".links"
    
    # Insert mock values
    obj_list = [get_test_object(1, pop_keys = ["object_data"]), get_test_object(2, pop_keys = ["object_data"]), get_test_object(3, pop_keys = ["object_data"])]
    l_list = [get_test_object_data(1), get_test_object_data(2), get_test_object_data(3)]
    insert_objects(obj_list, db_cursor, config)
    insert_links(l_list, db_cursor, config)

    # Correct deletes (general data + link)
    resp = await cli.delete("/objects/delete", json = {"object_ids": [1]})
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM {links}")
    assert db_cursor.fetchone() == (2,)
    assert db_cursor.fetchone() == (3,)
    assert not db_cursor.fetchone()

    resp = await cli.delete("/objects/delete", json = {"object_ids": [2, 3]})
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM {links}")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
