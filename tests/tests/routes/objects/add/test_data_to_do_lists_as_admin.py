"""
Tests for operations with to-do lists performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token


async def test_add(cli, db_cursor):
    correct_to_do_list_items = get_test_object(7, object_type="to_do_list")["object_data"]["items"]

    # Incorrect attributes
    for attr in [{"incorrect attr": "123"}, {"incorrect attr": "123", "sort_type": "default", "items": correct_to_do_list_items}]:
        tdl = get_test_object(7, object_type="to_do_list", pop_keys=["object_id", "created_at", "modified_at"])
        tdl["object_data"] = attr
        resp = await cli.post("/objects/add", json={"object": tdl}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attibutes (to-do list items, missing keys)
    for k in correct_to_do_list_items[0].keys():
        tdl = get_test_object(7, object_type="to_do_list", pop_keys=["object_id", "created_at", "modified_at"])
        tdl["object_data"]["items"][0].pop(k)
        resp = await cli.post("/objects/add", json={"object": tdl}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attibutes (to-do list items, additional key)
    tdl = get_test_object(7, object_type="to_do_list", pop_keys=["object_id", "created_at", "modified_at"])
    tdl["object_data"]["items"][0]["wrong_key"] = "some value"
    resp = await cli.post("/objects/add", json={"object": tdl}, headers=headers_admin_token)
    assert resp.status == 400
    
    # Incorrect attribute values (general to-do list object data)
    for k, v in [("sort_type", 1), ("sort_type", True), ("sort_type", "incorrect string"), ("items", 1), ("items", True), ("items", "string"), ("items", [])]:
        tdl = get_test_object(7, object_type="to_do_list", pop_keys=["object_id", "created_at", "modified_at"])
        tdl["object_data"][k] = v
        resp = await cli.post("/objects/add", json={"object": tdl}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute values (to-do list items)
    for k, v in [("item_number", "string"), ("item_number", -1), ("item_state", 0), ("item_state", "wrong value"), ("item_text", 0), ("commentary", 0),
                ("indent", "string"), ("indent", -1), ("is_expanded", 0), ("is_expanded", "string")]:
        tdl = get_test_object(7, object_type="to_do_list", pop_keys=["object_id", "created_at", "modified_at"])
        tdl["object_data"]["items"][0][k] = v
        resp = await cli.post("/objects/add", json={"object": tdl}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute values (to-do list items, duplicate line numbers)
    tdl = get_test_object(7, object_type="to_do_list", pop_keys=["object_id", "created_at", "modified_at"])
    tdl["object_data"]["items"][0]["item_number"] = tdl["object_data"]["items"][1]["item_number"]
    resp = await cli.post("/objects/add", json={"object": tdl}, headers=headers_admin_token)
    assert resp.status == 400

    for table in ["objects", "to_do_lists", "to_do_list_items"]:    # Check that a new object was not created
        db_cursor.execute(f"SELECT object_id FROM {table}") 
        assert not db_cursor.fetchone()
    
    # Add a correct to-do list object
    tdl = get_test_object(7, object_type="to_do_list", pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": tdl}, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert "object" in resp_json
    resp_object = resp_json["object"]

    # Check to_do_lists table
    db_cursor.execute(f"SELECT sort_type FROM to_do_lists WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (tdl["object_data"]["sort_type"],)
    
    # Check to_do_list_items table
    db_cursor.execute(f"SELECT * FROM to_do_list_items WHERE object_id = {resp_object['object_id']}")
    num_of_items = 0
    for row in db_cursor.fetchall():
        for item in tdl["object_data"]["items"]:
            if item["item_number"] == row[1]:  # fetchall returns tuple objects, so it's not possible to address columns by key
                assert tuple(item.values()) == row[1:]  # row[0] contains object_id
                num_of_items += 1
                break
    assert num_of_items == len(tdl["object_data"]["items"])


if __name__ == "__main__":
    run_pytest_tests(__file__)
