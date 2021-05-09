"""
Tests for operations with to-do lists.
"""
import os

from util import check_ids
from fixtures.objects import *


async def test_add(cli, db_cursor, config):
    schema = config["db"]["db_schema"]
    correct_to_do_list_items = get_test_object(7)["object_data"]["items"]

    # Incorrect attributes
    for attr in [{"incorrect attr": "123"}, {"incorrect attr": "123", "sort_type": "default", "items": correct_to_do_list_items}]:
        tdl = get_test_object(7, pop_keys = ["object_id", "created_at", "modified_at"])
        tdl["object_data"] = attr
        resp = await cli.post("/objects/add", json = {"object": tdl})
        assert resp.status == 400
    
    # Incorrect attibutes (to-do list items, missing keys)
    for k in correct_to_do_list_items[0].keys():
        tdl = get_test_object(7, pop_keys = ["object_id", "created_at", "modified_at"])
        tdl["object_data"]["items"][0].pop(k)
        resp = await cli.post("/objects/add", json = {"object": tdl})
        assert resp.status == 400
    
    # Incorrect attibutes (to-do list items, additional key)
    tdl = get_test_object(7, pop_keys = ["object_id", "created_at", "modified_at"])
    tdl["object_data"]["items"][0]["wrong_key"] = "some value"
    resp = await cli.post("/objects/add", json = {"object": tdl})
    assert resp.status == 400
    
    # Incorrect attribute values (general to-do list object data)
    for k, v in [("sort_type", 1), ("sort_type", True), ("sort_type", "incorrect string"), ("items", 1), ("items", True), ("items", "string"), ("items", [])]:
        tdl = get_test_object(7, pop_keys = ["object_id", "created_at", "modified_at"])
        tdl["object_data"][k] = v
        resp = await cli.post("/objects/add", json = {"object": tdl})
        assert resp.status == 400
    
    # Incorrect attribute values (to-do list items)
    for k, v in [("item_number", "string"), ("item_number", -1), ("item_state", 0), ("item_state", "wrong value"), ("item_text", 0), ("commentary", 0),
                ("indent", "string"), ("indent", -1), ("is_expanded", 0), ("is_expanded", "string")]:
        tdl = get_test_object(7, pop_keys = ["object_id", "created_at", "modified_at"])
        tdl["object_data"]["items"][0][k] = v
        resp = await cli.post("/objects/add", json = {"object": tdl})
        assert resp.status == 400
    
    # Incorrect attribute values (to-do list items, duplicate line numbers)
    tdl = get_test_object(7, pop_keys = ["object_id", "created_at", "modified_at"])
    tdl["object_data"]["items"][0]["item_number"] = tdl["object_data"]["items"][1]["item_number"]
    resp = await cli.post("/objects/add", json = {"object": tdl})
    assert resp.status == 400

    for table in ["objects", "to_do_lists", "to_do_list_items"]:    # Check that a new object was not created
        db_cursor.execute(f"SELECT object_id FROM {schema}.{table}") 
        assert not db_cursor.fetchone()
    
    # Add a correct to-do list object
    tdl = get_test_object(7, pop_keys = ["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json = {"object": tdl})
    assert resp.status == 200
    resp_json = await resp.json()
    assert "object" in resp_json
    resp_object = resp_json["object"]

    # Check to_do_lists table
    db_cursor.execute(f"SELECT sort_type FROM {schema}.to_do_lists WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (tdl["object_data"]["sort_type"],)
    
    # Check to_do_list_items table
    db_cursor.execute(f"SELECT * FROM {schema}.to_do_list_items WHERE object_id = {resp_object['object_id']}")
    num_of_items = 0
    for row in db_cursor.fetchall():
        for item in tdl["object_data"]["items"]:
            if item["item_number"] == row[1]:  # fetchall returns tuple objects, so it's not possible to address columns by key
                assert tuple(item.values()) == row[1:]  # row[0] contains object_id
                num_of_items += 1
                break
    assert num_of_items == len(tdl["object_data"]["items"])


async def test_update(cli, db_cursor, config):
    schema = config["db"]["db_schema"]
    correct_to_do_list_items = get_test_object(7)["object_data"]["items"]

    # Insert mock values
    obj_list = [get_test_object(7, pop_keys = ["object_data"]), get_test_object(8, pop_keys = ["object_data"])]
    tdl_list = [get_test_object_data(7), get_test_object_data(8)]
    insert_objects(obj_list, db_cursor, config)
    insert_to_do_lists(tdl_list, db_cursor, config)

    # Incorrect attributes
    for attr in [{"incorrect attr": "123"}, {"incorrect attr": "123", "sort_type": "default", "items": correct_to_do_list_items}]:
        tdl = get_test_object(7, pop_keys = ["created_at", "modified_at", "object_type"])
        tdl["object_data"] = attr
        resp = await cli.put("/objects/update", json = {"object": tdl})
        assert resp.status == 400
    
    # Incorrect attibutes (to-do list items, missing keys)
    for k in correct_to_do_list_items[0].keys():
        tdl = get_test_object(7, pop_keys = ["created_at", "modified_at", "object_type"])
        tdl["object_data"]["items"][0].pop(k)
        resp = await cli.put("/objects/update", json = {"object": tdl})
        assert resp.status == 400
    
    # Incorrect attibutes (to-do list items, additional key)
    tdl = get_test_object(7, pop_keys = ["created_at", "modified_at", "object_type"])
    tdl["object_data"]["items"][0]["wrong_key"] = "some value"
    resp = await cli.put("/objects/update", json = {"object": tdl})
    assert resp.status == 400
    
    # Incorrect attribute values (general to-do list object data)
    for k, v in [("sort_type", 1), ("sort_type", True), ("sort_type", "incorrect string"), ("items", 1), ("items", True), ("items", "string"), ("items", [])]:
        tdl = get_test_object(7, pop_keys = ["created_at", "modified_at", "object_type"])
        tdl["object_data"][k] = v
        resp = await cli.put("/objects/update", json = {"object": tdl})
        assert resp.status == 400
    
    # Incorrect attribute values (to-do list items)
    for k, v in [("item_number", "string"), ("item_number", -1), ("item_state", 0), ("item_state", "wrong value"), ("item_text", 0), ("commentary", 0),
                ("indent", "string"), ("indent", -1), ("is_expanded", 0), ("is_expanded", "string")]:
        tdl = get_test_object(7, pop_keys = ["created_at", "modified_at", "object_type"])
        tdl["object_data"]["items"][0][k] = v
        resp = await cli.put("/objects/update", json = {"object": tdl})
        assert resp.status == 400
    
    # Incorrect attribute values (to-do list items, duplicate line numbers)
    tdl = get_test_object(7, pop_keys = ["created_at", "modified_at", "object_type"])
    tdl["object_data"]["items"][0]["item_number"] = tdl["object_data"]["items"][1]["item_number"]
    resp = await cli.put("/objects/update", json = {"object": tdl})
    assert resp.status == 400
    
    # Correct update
    tdl = get_test_object(9, pop_keys = ["created_at", "modified_at", "object_type"])
    tdl["object_id"] = 7
    resp = await cli.put("/objects/update", json = {"object": tdl})
    assert resp.status == 200

    # Check to_do_lists table
    db_cursor.execute(f"SELECT sort_type FROM {schema}.to_do_lists WHERE object_id = {tdl['object_id']}")
    assert db_cursor.fetchone() == (tdl["object_data"]["sort_type"],)
    
    # Check to_do_list_items table
    db_cursor.execute(f"SELECT * FROM {schema}.to_do_list_items WHERE object_id = {tdl['object_id']}")
    num_of_items = 0
    for row in db_cursor.fetchall():
        for item in tdl["object_data"]["items"]:
            if item["item_number"] == row[1]:  # fetchall returns tuple objects, so it's not possible to address columns by key
                assert tuple(item.values()) == row[1:]  # row[0] contains object_id
                num_of_items += 1
                break
    assert num_of_items == len(tdl["object_data"]["items"])


async def test_view(cli, db_cursor, config):
    # Insert mock values
    insert_objects(get_objects_attributes_list(21, 30), db_cursor, config)
    insert_to_do_lists(to_do_lists_data_list, db_cursor, config)

    # Correct request (object_data_ids only, links), non-existing ids
    object_data_ids = [_ for _ in range(1001, 1011)]
    resp = await cli.post("/objects/view", json = {"object_data_ids": object_data_ids})
    assert resp.status == 404

    # Correct request (object_data_ids only, to-do lists)
    object_data_ids = [_ for _ in range(21, 31)]
    resp = await cli.post("/objects/view", json = {"object_data_ids": object_data_ids})
    assert resp.status == 200
    data = await resp.json()
    assert "object_data" in data

    # Check basic response attributes
    for field in ("object_id", "object_type", "object_data"):
        assert field in data["object_data"][0]
    
    # Check to-do list's general object data attributes
    for k in ["sort_type", "items"]:
        assert k in data["object_data"][0]["object_data"]
    
    # Check to-do list's item attributes
    for k in get_test_object(7)["object_data"]["items"][0].keys():
        assert k in data["object_data"][0]["object_data"]["items"][0]
    
    # Check ids
    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request, to-do lists object_data_ids only")


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
