"""
Tests for operations with to-do lists performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_object_attrs, get_test_object_data
from tests.data_generators.sessions import headers_admin_token
from tests.data_sets.objects import incorrect_to_do_list_attributes, incorrect_to_do_list_item_attributes
from tests.db_operations.objects import insert_objects, insert_to_do_lists


async def test_update(cli, db_cursor):
    correct_to_do_list_items = get_test_object(7, object_type="to_do_list")["object_data"]["items"]

    # Insert mock values
    obj_list = [get_object_attrs(i, object_type="to_do_list") for i in range(7, 9)]
    tdl_list = [get_test_object_data(i, object_type="to_do_list") for i in range(7, 9)]
    insert_objects(obj_list, db_cursor)
    insert_to_do_lists(tdl_list, db_cursor)

    # Missing required top-level attributes
    for attr in ["sort_type", "items"]:
        tdl = get_test_object(7, object_type="to_do_list", pop_keys=["created_at", "modified_at", "object_type"])
        tdl["object_data"].pop(attr)
        resp = await cli.put("/objects/update", json={"object": tdl}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect & unallowed top-level attributes
    for attr, values in incorrect_to_do_list_attributes.items():
        for value in values:
            tdl = get_test_object(7, object_type="to_do_list", pop_keys=["created_at", "modified_at", "object_type"])
            tdl["object_data"][attr] = value
            resp = await cli.put("/objects/update", json={"object": tdl}, headers=headers_admin_token)
            assert resp.status == 400
    
    # Incorrect and unallowed to-do list item attributes
    for attr, values in incorrect_to_do_list_item_attributes.items():
        for value in values:
            tdl = get_test_object(7, object_type="to_do_list", pop_keys=["created_at", "modified_at", "object_type"])
            tdl["object_data"]["items"][0][attr] = value
            resp = await cli.put("/objects/update", json={"object": tdl}, headers=headers_admin_token)
            assert resp.status == 400
    
    # Missing required to-do list item attributes
    for k in correct_to_do_list_items[0].keys():
        tdl = get_test_object(7, object_type="to_do_list", pop_keys=["created_at", "modified_at", "object_type"])
        tdl["object_data"]["items"][0].pop(k)
        resp = await cli.put("/objects/update", json={"object": tdl}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute values (to-do list items, duplicate line numbers)
    tdl = get_test_object(7, object_type="to_do_list", pop_keys=["created_at", "modified_at", "object_type"])
    tdl["object_data"]["items"][0]["item_number"] = tdl["object_data"]["items"][1]["item_number"]
    resp = await cli.put("/objects/update", json={"object": tdl}, headers=headers_admin_token)
    assert resp.status == 400
    
    # Correct update
    tdl = get_test_object(9, object_type="to_do_list", pop_keys=["created_at", "modified_at", "object_type"])
    tdl["object_id"] = 7
    resp = await cli.put("/objects/update", json={"object": tdl}, headers=headers_admin_token)
    assert resp.status == 200

    # Check to_do_lists table
    db_cursor.execute(f"SELECT sort_type FROM to_do_lists WHERE object_id = {tdl['object_id']}")
    assert db_cursor.fetchone() == (tdl["object_data"]["sort_type"],)
    
    # Check to_do_list_items table
    db_cursor.execute(f"SELECT * FROM to_do_list_items WHERE object_id = {tdl['object_id']}")
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
