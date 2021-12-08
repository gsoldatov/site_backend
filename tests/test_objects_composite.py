"""
Tests for composite objects' data operations.
"""
"""
Tests for link-specific operations.
"""
import pytest
from datetime import datetime

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))


from tests.util import check_ids
from tests.fixtures.objects import get_test_object, get_objects_attributes_list, get_test_object_data, get_composite_subobject_object_data, \
    add_composite_subobject, add_composite_deleted_subobject, composite_data_list, \
    insert_objects, insert_links, insert_markdown, insert_to_do_lists, insert_composite, insert_composite_properties, insert_data_for_view_objects_as_anonymous
from tests.fixtures.sessions import headers_admin_token
from tests.fixtures.users import get_test_user, insert_users


async def test_add_incorrect_top_level_data_as_admin(cli):
    # Missing attributes
    for attr in ["subobjects", "deleted_subobjects", "display_mode", "numerate_chapters"]:
        composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
        composite["object_data"].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed attributes
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["unallowed"] = 123
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect attribute values
    incorrect_value = {"subobjects": [1, False, "str", []], "deleted_subobjects": [1, False, "str"],
        "display_mode": [1, False, "wrong str"], "numerate_chapters": [1, "str", []]}
    for attr in ["subobjects", "deleted_subobjects", "display_mode", "numerate_chapters"]:
        for value in incorrect_value[attr]:
            composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
            composite["object_data"][attr] = value
            resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
            assert resp.status == 400


# Run the test twice for new & existing subobjects
@pytest.mark.parametrize("subobject_id", [-1, 5])
async def test_add_incorrect_subobject_attributes_as_admin(cli, db_cursor, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_test_object(subobject_id, owner_id=1, pop_keys=["object_data"])], db_cursor)
        insert_links([get_test_object_data(subobject_id, object_type="link")], db_cursor)
    
    # Missing attributes (no subobject update)
    for attr in ["object_id", "row", "column", "selected_tab", "is_expanded", "show_description_composite", "show_description_as_link_composite"]:
        composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
        composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
        composite["object_data"]["subobjects"][0].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed attributes (no subobject update)
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
    composite["object_data"]["subobjects"][0]["unallowed"] = 123
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values (no subobject update)
    _inc_val_default = ["str", False, -1, 3.14]
    incorrect_values = {"object_id": ["str", False, 3.14], "row": _inc_val_default, "column": _inc_val_default, 
        "selected_tab": _inc_val_default, "is_expanded": ["str", 1], 
        "show_description_composite": [1, False, "wrong str"], "show_description_as_link_composite": [1, False, "wrong str"]}
    for attr in ["object_id", "row", "column", "selected_tab", "is_expanded", "show_description_composite", "show_description_as_link_composite"]:
        for value in incorrect_values[attr]:
            composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
            composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
            composite["object_data"]["subobjects"][0][attr] = value
            resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
            assert resp.status == 400
    
    # Missing attributes (with subobject update)
    for attr in ["object_id", "row", "column", "selected_tab", "is_expanded", 
        "object_name", "object_description", "object_type", "is_published", "display_in_feed", "feed_timestamp", "show_description", "object_data"]:
        composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
        composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
        composite["object_data"]["subobjects"][0].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect values (with subobject update)
    incorrect_values = {
        "object_id": ["str", False, 3.14], "row": _inc_val_default, "column": _inc_val_default, "selected_tab": _inc_val_default, "is_expanded": ["str", 1],
        "object_name": [False, 1, "", "a"*256], "object_description": [False, 1], "object_type": [1, False, "unallowed"], 
        "is_published": [1, "str"], "display_in_feed": [1, "str"], "feed_timestamp": [1, True, "non date str", "99999-12-31"], 
        "show_description": [1, "str"], "object_data": [1, False, "unallowed"], "owner_id": [0, "str", False]
    }
    for attr in incorrect_values:
        for value in incorrect_values[attr]:
            composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
            composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
            composite["object_data"]["subobjects"][0][attr] = value
            resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
            assert resp.status == 400


# Run the test twice for new & existing subobjects
@pytest.mark.parametrize("subobject_id", [-1, 5])
async def test_add_incorrect_subobject_object_data_link_as_admin(cli, db_cursor, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_test_object(subobject_id, owner_id=1, object_type="link", pop_keys=["object_data"])], db_cursor)
        insert_links([get_test_object_data(subobject_id, object_type="link")], db_cursor)
    
    # Missing subobject object_data attributes
    for attr in ["link", "show_description_as_link"]:
        composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
        composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
        composite["object_data"]["subobjects"][0]["object_data"].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400

    # Unallowed subobject object_data attributes (link)
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
    composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
    composite["object_data"]["subobjects"][0]["object_data"]["unallowed"] = "str"
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


# Run the test twice for new & existing subobjects
@pytest.mark.parametrize("subobject_id", [-1, 5])
async def test_add_incorrect_subobject_object_data_markdown_as_admin(cli, db_cursor, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_test_object(subobject_id, owner_id=1, object_type="markdown", pop_keys=["object_data"])], db_cursor)
        insert_markdown([get_test_object_data(subobject_id, object_type="markdown")], db_cursor)
    
    # Missing subobject object_data attributes (markdown)
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
    composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
    composite["object_data"]["subobjects"][0]["object_type"] = "markdown"
    composite["object_data"]["subobjects"][0]["object_data"] = get_composite_subobject_object_data(4, object_type="markdown")
    composite["object_data"]["subobjects"][0]["object_data"].pop("raw_text")
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400

    # Unallowed subobject object_data attributes (markdown)
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
    composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
    composite["object_data"]["subobjects"][0]["object_type"] = "markdown"
    composite["object_data"]["subobjects"][0]["object_data"] = get_composite_subobject_object_data(4, object_type="markdown")
    composite["object_data"]["subobjects"][0]["object_data"]["unallowed"] = "str"
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


# Run the test twice for new & existing subobjects
@pytest.mark.parametrize("subobject_id", [-1, 5])
async def test_add_incorrect_subobject_object_data_to_do_list_as_admin(cli, db_cursor, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_test_object(subobject_id, owner_id=1, object_type="to_do_list", pop_keys=["object_data"])], db_cursor)
        insert_to_do_lists([get_test_object_data(subobject_id, object_type="to_do_list")], db_cursor)
    
    # Missing subobject object_data attributes (to-do list)
    for attr in ["sort_type", "items"]:
        composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
        composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
        composite["object_data"]["subobjects"][0]["object_type"] = "to_do_list"
        composite["object_data"]["subobjects"][0]["object_data"] = get_composite_subobject_object_data(7)
        composite["object_data"]["subobjects"][0]["object_data"].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed subobject object_data attributes (to-do list)
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
    composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
    composite["object_data"]["subobjects"][0]["object_type"] = "to_do_list"
    composite["object_data"]["subobjects"][0]["object_data"] = get_composite_subobject_object_data(7)
    composite["object_data"]["subobjects"][0]["object_data"]["unallowed"] = "str"
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_incorrect_deleted_subobjects_data_as_admin(cli):
    # Missing attributes
    for attr in ["object_id", "is_full_delete"]:
        composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
        composite["object_data"]["deleted_subobjects"] = [{"object_id": 1, "is_full_delete": True}]
        composite["object_data"]["deleted_subobjects"][0].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed attributes
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["deleted_subobjects"] = [{"object_id": 1, "is_full_delete": True, "unallowed": "str"}]
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    incorrect_values = {"object_id": ["str", True, 0], "is_full_delete": ["str", 0]}
    for attr in incorrect_values:
        for value in incorrect_values[attr]:
            composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
            composite["object_data"]["deleted_subobjects"] = [{"object_id": 1, "is_full_delete": True}]
            composite["object_data"]["deleted_subobjects"][0][attr] = value
            resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
            assert resp.status == 400


async def test_add_validation_non_unique_subobject_ids_as_admin(cli):
    # Non-unique subobject ids
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, 1)
    add_composite_subobject(composite, 1)
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_validation_missing_new_subobjects_attributes_as_admin(cli):
    # New subobject without attributes/data
    for attr in ["object_name", "object_description", "object_type", "is_published", "display_in_feed", "feed_timestamp", "show_description", "object_data"]:
        composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
        composite["object_data"]["subobjects"] = []
        add_composite_subobject(composite, object_id=-1, object_name="name", object_description="descr", 
            is_published=False, show_description=True, object_type="link", object_data=get_composite_subobject_object_data(1))
        composite["object_data"]["subobjects"][0].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400


async def test_add_validation_not_existing_subobject_as_admin(cli):
    # Positive subobject id, which does not exist in the database
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=999)
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_validation_not_existing_updated_subobject_as_admin(cli, db_cursor):
    # Positive subobject id with updated attributes/data, which does not exist in the database
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=999, object_name="name", object_description="descr", 
        is_published=False, show_description=True, object_type="link", object_data=get_composite_subobject_object_data(1, object_type="link"))
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400

    # Check if composite object was not added
    db_cursor.execute(f"SELECT object_id FROM objects WHERE object_type = 'composite'")
    assert not db_cursor.fetchone()
    

async def test_add_validation_incorrect_updated_subobject_type_as_admin(cli, db_cursor):
    # Insert objects
    obj_list = [get_test_object(100, owner_id=1, object_type="link", pop_keys=["object_data"]),
                get_test_object(101, owner_id=1, object_type="markdown", pop_keys=["object_data"]),
                get_test_object(102, owner_id=1, object_type="to_do_list", pop_keys=["object_data"])]
    insert_objects(obj_list, db_cursor)

    # Try updating a non-existing link subobject data
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=101, object_name="name", object_description="descr", 
        is_published=False, show_description=True, object_type="link", object_data=get_composite_subobject_object_data(1))
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400
    db_cursor.execute(f"SELECT object_id FROM objects WHERE object_type = 'composite'")
    assert not db_cursor.fetchone()

    # Try updating a non-existing Markdown subobject data
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=100, object_name="name", object_description="descr", 
        is_published=False, show_description=True, object_type="markdown", object_data=get_composite_subobject_object_data(6))
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400
    db_cursor.execute(f"SELECT object_id FROM objects WHERE object_type = 'composite'")
    assert not db_cursor.fetchone()

    # Try updating a non-existing to-do list subobject data
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=100, object_name="name", object_description="descr", 
        is_published=False, show_description=True, object_type="to_do_list", object_data=get_composite_subobject_object_data(9))
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400
    db_cursor.execute(f"SELECT object_id FROM objects WHERE object_type = 'composite'")
    assert not db_cursor.fetchone()


async def test_add_validation_non_unique_subobject_row_column_combinaiton_as_admin(cli):
    # Non unique row + column combination
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=1, row=0, column=0)
    add_composite_subobject(composite, object_id=2, row=0, column=0)
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_validation_same_id_in_subobjects_and_deleted_subobjects_as_admin(cli):
    # object id present both in subobjects and deleted_subobjects
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=1)
    add_composite_deleted_subobject(composite, 999, True)
    add_composite_deleted_subobject(composite, 1, True)
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


# Run the test twice for new & existing subobjects
@pytest.mark.parametrize("subobject_id", [-1, 5])
async def test_add_subobject_with_a_non_existing_owner_id_as_admin(cli, db_cursor, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_test_object(subobject_id, owner_id=1, object_type="link", pop_keys=["object_data"])], db_cursor)
        insert_links([get_test_object_data(subobject_id, object_type="link")], db_cursor)
    
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=subobject_id, is_expanded=False, object_name="subobject name", object_description="subobject descr", 
                            is_published=True, show_description=True, object_type="link", owner_id=1000, object_data=get_composite_subobject_object_data(1, object_type="link"))
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_correct_object_without_subobject_updates_as_admin(cli, db_cursor):
    # Insert objects
    obj_list = [get_test_object(100 + i, owner_id=1, object_type="link", pop_keys=["object_data"]) for i in range(5)]
    insert_objects(obj_list, db_cursor)

    # Add a composite object without subobjects update
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=100)
    add_composite_subobject(composite, object_id=101)
    add_composite_subobject(composite, object_id=102)
    add_composite_subobject(composite, object_id=103, column=1)
    add_composite_subobject(composite, object_id=104, column=1)
    
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200

    # Check database state
    resp_object = (await resp.json())["object"]
    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = {resp_object['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == sorted([o["object_id"] for o in obj_list])


async def test_add_correct_object_with_new_subobjects_as_admin(cli, db_cursor):
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user

    # Send request with new subobjects
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=-1, is_expanded=False, object_name="new link 1", object_description="new descr 1", 
                            is_published=True, display_in_feed=True, show_description=True, object_type="link", object_data=get_composite_subobject_object_data(1))
    add_composite_subobject(composite, object_id=-2, is_expanded=False, object_name="new markdown 1", object_description="new descr 2", 
                            is_published=True, display_in_feed=False, show_description=False, object_type="markdown", object_data=get_composite_subobject_object_data(4))
    add_composite_subobject(composite, object_id=-3, is_expanded=False, object_name="new to-do list 1", object_description="new descr 3", 
                            is_published=True, display_in_feed=True, show_description=True, object_type="to_do_list", object_data=get_composite_subobject_object_data(7))
    add_composite_subobject(composite, object_id=-4, column=1, object_name="new link 2", object_description="new descr 4", 
                            is_published=False, display_in_feed=False, show_description=False, object_type="link", owner_id=2, object_data=get_composite_subobject_object_data(2))
    add_composite_subobject(composite, object_id=-5, column=1, object_name="new markdown 2", object_description="new descr 5", 
                            is_published=False, display_in_feed=True, show_description=True, object_type="markdown", owner_id=2, object_data=get_composite_subobject_object_data(5))
    add_composite_subobject(composite, object_id=-6, column=1, object_name="new to-do list 2", object_description="new descr 6", 
                            is_published=False, display_in_feed=False, show_description=False, object_type="to_do_list", owner_id=2, object_data=get_composite_subobject_object_data(8))
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200

    # Check response data and new subobjects' attributes in the database
    resp_json = await resp.json()
    assert "object_data" in resp_json["object"]
    assert "id_mapping" in resp_json["object"]["object_data"]
    id_mapping, subobjects = resp_json["object"]["object_data"]["id_mapping"], {}
    assert len(id_mapping) == len(composite["object_data"]["subobjects"])
    for obj_id in id_mapping:
        for so in composite["object_data"]["subobjects"]:
            if int(obj_id) == so["object_id"]:
                subobjects[id_mapping[obj_id]] = so
                break
    
    db_cursor.execute(f"""SELECT object_id, object_name, object_description, object_type, is_published, display_in_feed, feed_timestamp,
        show_description, owner_id FROM objects WHERE object_id IN {tuple(id_mapping.values())}""")
    result = db_cursor.fetchall()
    assert len(result) == len(id_mapping)
    for row in result:
        object_id = row[0]
        assert subobjects[object_id]["object_name"] == row[1]
        assert subobjects[object_id]["object_description"] == row[2]
        assert subobjects[object_id]["object_type"] == row[3]
        assert subobjects[object_id]["is_published"] == row[4]
        assert subobjects[object_id]["display_in_feed"] == row[5]
        assert datetime.fromisoformat(subobjects[object_id]["feed_timestamp"][:-1]) == row[6]
        assert subobjects[object_id]["show_description"] == row[7]
        assert subobjects[object_id].get("owner_id", 1) == row[8]   # If owner_id is not set in request, token owner should be set as owner_id of new object
    
    # Check new subobjects' data in the database
    for object_id in subobjects:
        object_type = subobjects[object_id]["object_type"]
        if object_type == "link":
            db_cursor.execute(f"SELECT link FROM links WHERE object_id = {object_id}")
            assert db_cursor.fetchone()[0] == subobjects[object_id]["object_data"]["link"]
        elif object_type == "markdown":
            db_cursor.execute(f"SELECT raw_text FROM markdown WHERE object_id = {object_id}")
            assert db_cursor.fetchone()[0] == subobjects[object_id]["object_data"]["raw_text"]
        elif object_type == "to_do_list":
            db_cursor.execute(f"SELECT item_text FROM to_do_list_items WHERE object_id = {object_id} ORDER BY item_number")
            result = db_cursor.fetchall()
            assert len(result) == len(subobjects[object_id]["object_data"]["items"])
            assert subobjects[object_id]["object_data"]["items"][0]["item_text"] == result[0][0]
            
    
    # Check composite object's subobjects in the database
    db_cursor.execute(f"SELECT subobject_id, row, \"column\", selected_tab, is_expanded, show_description_composite, show_description_as_link_composite FROM composite WHERE object_id = {resp_json['object']['object_id']}")
    result = db_cursor.fetchall()
    assert len(result) == len(id_mapping)
    for row in result:
        subobject_id = row[0]
        assert subobjects[subobject_id]["row"] == row[1]
        assert subobjects[subobject_id]["column"] == row[2]
        assert subobjects[subobject_id]["selected_tab"] == row[3]
        assert subobjects[subobject_id]["is_expanded"] == row[4]
        assert subobjects[subobject_id]["show_description_composite"] == row[5]
        assert subobjects[subobject_id]["show_description_as_link_composite"] == row[6]


async def test_add_correct_object_update_existing_subobjects_as_admin(cli, db_cursor):
    insert_users([get_test_user(2, pop_keys=["password_repeat"]), get_test_user(3, pop_keys=["password_repeat"])], db_cursor) # add users
    default_owner = 2

    # Insert objects' attributes and data
    obj_list = [get_test_object(100, owner_id=default_owner, is_published=False, object_type="link", pop_keys=["object_data"]), 
                get_test_object(101, owner_id=default_owner, is_published=True, object_type="markdown", pop_keys=["object_data"]),
                get_test_object(102, owner_id=default_owner, is_published=False, object_type="to_do_list", pop_keys=["object_data"])]
    insert_objects(obj_list, db_cursor)
    link_data = [get_test_object_data(100, object_type="link")]
    markdown_data = [get_test_object_data(101, object_type="markdown")]
    to_do_list_data = [get_test_object_data(102, object_type="to_do_list")]
    to_do_list_data[0]["object_data"]["items"][0]["item_text"] = "updated item text"
    insert_links(link_data, db_cursor)
    insert_markdown(markdown_data, db_cursor)
    insert_to_do_lists(to_do_list_data, db_cursor)

    # Send request with updates for existing subobjects
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=100, object_name="updated link name", object_description="updated link descr", 
                            is_published=True, display_in_feed=True, show_description=True, object_type="link", owner_id=3, object_data=get_composite_subobject_object_data(1))
    add_composite_subobject(composite, object_id=101, object_name="updated markdown name", object_description="updated mardkown descr", 
                            is_published=False, display_in_feed=False, show_description=False, object_type="markdown", owner_id=1, object_data=get_composite_subobject_object_data(4))
    add_composite_subobject(composite, object_id=102, object_name="updated to-do list name", object_description="updated to-do list descr", 
                            is_published=True, display_in_feed=True, show_description=True, object_type="to_do_list", object_data=get_composite_subobject_object_data(7))
    
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200

    # Check if subobjects' attributes are updated
    subobjects = {so["object_id"]: so for so in composite["object_data"]["subobjects"]}
    db_cursor.execute(f"""SELECT object_id, object_name, object_description, object_type, is_published, display_in_feed, feed_timestamp,
        show_description, owner_id FROM objects WHERE object_id IN {tuple(subobjects.keys())}""")
    for row in db_cursor.fetchall():
        object_id = row[0]
        assert subobjects[object_id]["object_name"] == row[1]
        assert subobjects[object_id]["object_description"] == row[2]
        assert subobjects[object_id]["object_type"] == row[3]
        assert subobjects[object_id]["is_published"] == row[4]
        assert subobjects[object_id]["display_in_feed"] == row[5]
        assert datetime.fromisoformat(subobjects[object_id]["feed_timestamp"][:-1]) == row[6]
        assert subobjects[object_id]["show_description"] == row[7]
        assert subobjects[object_id].get("owner_id", default_owner) == row[8]   # If owner_id is not set in request, it should not be changed

    # Check if subobjects' data is updated
    for object_id in subobjects:
        object_type = subobjects[object_id]["object_type"]
        if object_type == "link":
            db_cursor.execute(f"SELECT link FROM links WHERE object_id = {object_id}")
            assert db_cursor.fetchone()[0] == subobjects[object_id]["object_data"]["link"]
        elif object_type == "markdown":
            db_cursor.execute(f"SELECT raw_text FROM markdown WHERE object_id = {object_id}")
            assert db_cursor.fetchone()[0] == subobjects[object_id]["object_data"]["raw_text"]
        elif object_type == "to_do_list":
            db_cursor.execute(f"SELECT item_text FROM to_do_list_items WHERE object_id = {object_id} ORDER BY item_number")
            result = db_cursor.fetchall()
            assert len(result) == len(subobjects[object_id]["object_data"]["items"])
            assert subobjects[object_id]["object_data"]["items"][0]["item_text"] == result[0][0]    


@pytest.mark.parametrize("owner_id", [1, 2])   # Run the test for the same and a new owner_id values
@pytest.mark.parametrize("subobject_id", [-1, 5])   # Run the test for new & existing subobject
async def test_add_correct_subobject_with_a_specified_owner_id_as_admin(cli, db_cursor, owner_id, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_test_object(subobject_id, owner_id=1, object_type="link", pop_keys=["object_data"])], db_cursor)
        insert_links([get_test_object_data(subobject_id, object_type="link")], db_cursor)
    # Insert another user
    if owner_id == 2:
        insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user
    
    composite = get_test_object(10, pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=subobject_id, is_expanded=False, object_name="subobject name", object_description="subobject descr", 
                            is_published=True, show_description=True, object_type="link", owner_id=owner_id, object_data=get_composite_subobject_object_data(1))
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    mapped_subobject_id = subobject_id if subobject_id > 0 else (await resp.json())["object"]["object_data"]["id_mapping"][str(subobject_id)]
    db_cursor.execute(f"SELECT owner_id FROM objects WHERE object_id = {mapped_subobject_id}")
    assert db_cursor.fetchone() == (owner_id, )


# Update handler uses the same logic as add handler, so tests are not duplicated
async def test_update_correct_object_without_subobject_updates_as_admin(cli, db_cursor):
    """Update composite subobject without updating its subobjects data"""
    # Insert objects
    obj_list = [get_test_object(100 + i, owner_id=1, object_type="link", pop_keys=["object_data"]) for i in range(5)]
    obj_list.append(get_test_object(10, owner_id=1, object_type="composite", pop_keys=["object_data"]))
    insert_objects(obj_list, db_cursor)

    # Insert existing composite object data
    composite_data = get_test_object_data(10, object_type="composite")
    composite_data["object_data"]["subobjects"] = []
    add_composite_subobject(composite_data, object_id=100)
    add_composite_subobject(composite_data, object_id=101)
    insert_composite([composite_data], db_cursor)

    # Update a composite object without subobjects update
    composite = get_test_object(10, object_type="composite", pop_keys=["object_type", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=102)
    add_composite_subobject(composite, object_id=103, column=1)
    add_composite_subobject(composite, object_id=104, column=1)

    resp = await cli.put("/objects/update", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200

    # Check database state
    resp_object = (await resp.json())["object"]
    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = {resp_object['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == sorted([o["object_id"] for o in composite["object_data"]["subobjects"]])


async def test_update_correct_object_with_subobject_full_and_not_full_delete_as_admin(cli, db_cursor):
    # Insert objects
    obj_list = [get_test_object(100 + i, owner_id=1, object_type="link", pop_keys=["object_data"]) for i in range(4)]   # 4 subobjects
    obj_list.extend([get_test_object(10 + i, owner_id=1, object_type="composite", pop_keys=["object_data"]) for i in range(2)]) # 2 composite objects
    insert_objects(obj_list, db_cursor)

    # Insert composite data (10: 100, 101, 102, 103; 11: 103)
    composite_data = get_test_object_data(10, object_type="composite")
    composite_data["object_data"]["subobjects"] = []
    for i in range(4):
        add_composite_subobject(composite_data, object_id=100 + i)
    insert_composite([composite_data], db_cursor)

    composite_data = get_test_object_data(11, object_type="composite")
    composite_data["object_data"]["subobjects"] = []
    add_composite_subobject(composite_data, object_id=103)
    insert_composite([composite_data], db_cursor)

    # Update first composite object (1 subobject remain & 2 subobjects are marked as fully deleted (one is present in the second object))
    composite = get_test_object(10, object_type="composite", pop_keys=["object_type", "created_at", "modified_at"])
    composite["object_data"]["subobjects"] = []
    add_composite_subobject(composite, object_id=100)
    composite["object_data"]["deleted_subobjects"] = [{ "object_id": 102, "is_full_delete": True }, { "object_id": 103, "is_full_delete": True }]

    resp = await cli.put("/objects/update", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200

    # Check database
    db_cursor.execute(f"SELECT object_id FROM objects")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [10, 11, 100, 101, 103]  # 102 and 103 were marked for full deletion; 103 was not deleted, because it's still a subobject of 11;
                                                                                    # 101 was deleted without full deletion and, thus, remains in the database
    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = 10")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [100]    # 101 was deleted; 102 and 103 were fully deleted

    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = 11")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [103]    # subobjects of 11 are not changed


async def test_view_composite_objects_as_admin(cli, db_cursor):
    # Insert mock values
    insert_objects(get_objects_attributes_list(1, 40), db_cursor)
    insert_composite(composite_data_list, db_cursor)

    # Correct request (object_data_ids only, composite), non-existing ids
    object_data_ids = [_ for _ in range(1001, 1011)]
    resp = await cli.post("/objects/view", json={"object_data_ids": object_data_ids}, headers=headers_admin_token)
    assert resp.status == 404

    # Correct request (object_data_ids only, composite)
    object_data_ids = [_ for _ in range(31, 41)]
    resp = await cli.post("/objects/view", json={"object_data_ids": object_data_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "object_data" in data

    for field in ("object_id", "object_type", "object_data"):
        assert field in data["object_data"][0]
    assert "subobjects" in data["object_data"][0]["object_data"]

    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request, composite object_data_ids only")
    
    for attr in ["object_id", "row", "column", "selected_tab", "is_expanded", "show_description_composite", "show_description_as_link_composite"]:
        assert attr in data["object_data"][0]["object_data"]["subobjects"][0]


async def test_view_composite_objects_without_subobjects_as_admin(cli, db_cursor):
    # Insert 2 objects (link & composite) + link data + composite properties
    obj_list = [get_test_object(10, owner_id=1, object_type="link", pop_keys=["object_data"]),
                get_test_object(11, owner_id=1, object_type="composite", pop_keys=["object_data"])]
    insert_objects(obj_list, db_cursor)

    link_data = [get_test_object_data(10, object_type="link")]
    insert_links(link_data, db_cursor)

    composite_data = [get_test_object_data(11, object_type="composite")]
    insert_composite_properties(composite_data, db_cursor)

    # Query data of both objects
    object_data_ids = [10, 11]
    resp = await cli.post("/objects/view", json={"object_data_ids": object_data_ids}, headers=headers_admin_token)

    assert resp.status == 200
    data = await resp.json()
    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, composite objects without subobjects")
    for object_data in data["object_data"]:
        object_id = object_data["object_id"]
        assert object_id in object_data_ids
        object_data_ids.remove(object_id)

        if object_id == 10:
            assert object_data["object_type"] == "link"
        else: # 11
            assert object_data["object_type"] == "composite"
            assert "subobjects" in object_data["object_data"]
            assert object_data["object_data"]["subobjects"] == []


async def test_view_composite_as_anonymous(cli, db_cursor):
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user
    object_attributes = [get_test_object(1, owner_id=1, pop_keys=["object_data"])]
    object_attributes.extend([get_test_object(i, object_type="composite", is_published=i % 2 == 0,
        owner_id=1 if i <= 35 else 2, pop_keys=["object_data"]) for i in range(31, 41)])
    insert_objects(object_attributes, db_cursor)
    composite_object_data = [get_test_object_data(i, object_type="composite") for i in range(31, 41)]
    insert_composite(composite_object_data, db_cursor)

    # Correct request (object_data_ids only, composite, request all composite objects, receive only published)
    requested_object_ids = [i for i in range(31, 41)]
    expected_object_ids = [i for i in range(31, 41) if i % 2 == 0]
    resp = await cli.post("/objects/view", json={"object_data_ids": requested_object_ids})
    assert resp.status == 200
    data = await resp.json()

    check_ids(expected_object_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as anonymous, composite object_data_ids only")


async def test_delete_composite_as_admin(cli, db_cursor):
    # Insert mock objects (composite: 10, 11; links: 101, 102, 103)
    obj_list = [get_test_object(100 + i, owner_id=1, object_type="link", pop_keys=["object_data"]) for i in range(1, 4)]   # 3 subobjects
    obj_list.extend([get_test_object(10 + i, owner_id=1, object_type="composite", pop_keys=["object_data"]) for i in range(2)]) # 2 composite objects
    insert_objects(obj_list, db_cursor)

    # Insert composite data (10: 101, 102, 103; 11: 103)
    composite_data = get_test_object_data(10, object_type="composite")
    composite_data["object_data"]["subobjects"] = []
    for i in range(1, 4):
        add_composite_subobject(composite_data, object_id=100 + i)
    insert_composite([composite_data], db_cursor)

    composite_data = get_test_object_data(11, object_type="composite")
    composite_data["object_data"]["subobjects"] = []
    add_composite_subobject(composite_data, object_id=103)
    insert_composite([composite_data], db_cursor)

    # Delete composite
    resp = await cli.delete("/objects/delete", json={"object_ids": [10] }, headers=headers_admin_token)
    assert resp.status == 200

    # Check database
    db_cursor.execute(f"SELECT object_id FROM objects")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [11, 101, 102, 103]    # 10 was deleted, but its subobjects were not

    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = 10")
    assert not db_cursor.fetchall()

    db_cursor.execute(f"SELECT object_id FROM composite_properties WHERE object_id = 10")
    assert not db_cursor.fetchall()

    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = 11")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [103]    # subobjects of 11 are not changed

    db_cursor.execute(f"SELECT object_id FROM composite_properties WHERE object_id = 11")
    assert len([r for r in db_cursor.fetchall()]) == 1


async def test_delete_with_subobjects_as_admin(cli, db_cursor):
    # Insert mock objects (composite: 10, 11; links: 100, 101, 102, 103)
    obj_list = [get_test_object(100 + i, owner_id=1, object_type="link", pop_keys=["object_data"]) for i in range(4)]   # 1 non-subobject + 3 subobjects
    obj_list.extend([get_test_object(10 + i, owner_id=1, object_type="composite", pop_keys=["object_data"]) for i in range(2)]) # 2 composite objects
    insert_objects(obj_list, db_cursor)

    # Insert composite data (10: 101, 102, 103; 11: 103)
    composite_data = get_test_object_data(10, object_type="composite")
    composite_data["object_data"]["subobjects"] = []
    for i in range(1, 4):
        add_composite_subobject(composite_data, object_id=100 + i)
    insert_composite([composite_data], db_cursor)

    composite_data = get_test_object_data(11, object_type="composite")
    composite_data["object_data"]["subobjects"] = []
    add_composite_subobject(composite_data, object_id=103)
    insert_composite([composite_data], db_cursor)

    # Delete with subobjects: first composite (10), 1 non-subobject link (100) and 1 of its exclusive subobjects (101)
    resp = await cli.delete("/objects/delete", json={"object_ids": [10, 100, 101], "delete_subobjects": True }, headers=headers_admin_token)
    assert resp.status == 200

    # Check database
    db_cursor.execute(f"SELECT object_id FROM objects")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [11, 103]    # 10, 100 and 101 were deleted, 102 was deleted since it was an exclusive subobject of 10

    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = 10")
    assert not db_cursor.fetchall()

    db_cursor.execute(f"SELECT object_id FROM composite_properties WHERE object_id = 10")
    assert not db_cursor.fetchall()

    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = 11")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [103]    # subobjects of 11 are not changed

    db_cursor.execute(f"SELECT object_id FROM composite_properties WHERE object_id = 11")
    assert len([r for r in db_cursor.fetchall()]) == 1


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')