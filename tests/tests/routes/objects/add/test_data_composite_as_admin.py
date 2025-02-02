"""
Tests for composite objects' data operations performed as admin.
"""
import pytest
from datetime import datetime, timezone, timedelta

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_object_attrs, get_test_object_data, \
    get_composite_data, get_composite_subobject_data, get_deleted_subobject, \
    get_link_data, get_markdown_data, get_to_do_list_data, get_to_do_list_item_data
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.users import get_test_user

from tests.db_operations.objects import insert_objects, insert_links, insert_markdown, insert_to_do_lists
from tests.db_operations.users import insert_users


async def test_add_incorrect_top_level_data(cli):
    # Missing attributes
    for attr in ["subobjects", "deleted_subobjects", "display_mode", "numerate_chapters"]:
        composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"])
        composite["object_data"].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed attributes
    composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["unallowed"] = 123
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect attribute values
    incorrect_value = {"subobjects": [1, False, "str", []], "deleted_subobjects": [1, False, "str"],
        "display_mode": [1, False, "wrong str"], "numerate_chapters": [1, "str", []]}
    for attr in ["subobjects", "deleted_subobjects", "display_mode", "numerate_chapters"]:
        for value in incorrect_value[attr]:
            composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"])
            composite["object_data"][attr] = value
            resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
            assert resp.status == 400


# Run the test twice for new & existing subobjects
@pytest.mark.parametrize("subobject_id", [-1, 5])
async def test_add_incorrect_subobject_attributes(cli, db_cursor, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_object_attrs(subobject_id)], db_cursor)
        insert_links([get_test_object_data(subobject_id)], db_cursor)
    
    # Missing attributes (no subobject update)
    for attr in ["subobject_id", "row", "column", "selected_tab", "is_expanded", "show_description_composite", "show_description_as_link_composite"]:
        composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"])
        composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
        composite["object_data"]["subobjects"][0].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed attributes (no subobject update)
    composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
    composite["object_data"]["subobjects"][0]["unallowed"] = 123
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values (no subobject update)
    _inc_val_default = ["str", False, -1, 3.14]
    incorrect_values = {"subobject_id": ["str", False, 3.14], "row": _inc_val_default, "column": _inc_val_default, 
        "selected_tab": _inc_val_default, "is_expanded": ["str", 1], 
        "show_description_composite": [1, False, "wrong str"], "show_description_as_link_composite": [1, False, "wrong str"]}
    for attr in ["subobject_id", "row", "column", "selected_tab", "is_expanded", "show_description_composite", "show_description_as_link_composite"]:
        for value in incorrect_values[attr]:
            composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"])
            composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
            composite["object_data"]["subobjects"][0][attr] = value
            resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
            assert resp.status == 400
    
    # Missing attributes (with subobject update)
    for attr in ["subobject_id", "row", "column", "selected_tab", "is_expanded", 
        "object_name", "object_description", "object_type", "is_published", "display_in_feed", "feed_timestamp", "show_description", "object_data"]:
        composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
        composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
        composite["object_data"]["subobjects"][0].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect values (with subobject update)
    incorrect_values = {
        "subobject_id": ["str", False, 3.14], "row": _inc_val_default, "column": _inc_val_default, "selected_tab": _inc_val_default, "is_expanded": ["str", 1],
        "object_name": [False, 1, "", "a"*256], "object_description": [False, 1], "object_type": [1, False, "unallowed"], 
        "is_published": [1, "str"], "display_in_feed": [1, "str"], "feed_timestamp": [1, True, "non date str", "99999-12-31"], 
        "show_description": [1, "str"], "object_data": [1, False, "unallowed"], "owner_id": [0, "str", False]
    }
    for attr in incorrect_values:
        for value in incorrect_values[attr]:
            composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
            composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
            composite["object_data"]["subobjects"][0][attr] = value
            resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
            assert resp.status == 400


# Run the test twice for new & existing subobjects
@pytest.mark.parametrize("subobject_id", [-1, 5])
async def test_add_incorrect_subobject_object_data_link(cli, db_cursor, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_object_attrs(subobject_id)], db_cursor)
        insert_links([get_test_object_data(subobject_id)], db_cursor)
    
    # Missing subobject object_data attributes
    for attr in ["link", "show_description_as_link"]:
        composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
        composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
        composite["object_data"]["subobjects"][0]["object_data"].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400

    # Unallowed subobject object_data attributes (link)
    composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"], composite_subobject_object_type="link")
    composite["object_data"]["subobjects"][0]["subobject_id"] = subobject_id
    composite["object_data"]["subobjects"][0]["object_data"]["unallowed"] = "str"
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


# Run the test twice for new & existing subobjects
@pytest.mark.parametrize("subobject_id", [-1, 5])
async def test_add_incorrect_subobject_object_data_markdown(cli, db_cursor, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_test_object(subobject_id, owner_id=1, object_type="markdown", pop_keys=["object_data"])], db_cursor)
        insert_markdown([get_test_object_data(subobject_id, object_type="markdown")], db_cursor)
    
    # Missing subobject object_data attributes (markdown)
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(subobjects=[get_composite_subobject_data(4, 0, 0, object_type="markdown")]),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    composite["object_data"]["subobjects"][0]["object_data"].pop("raw_text")
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400

    # Unallowed subobject object_data attributes (markdown)
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(subobjects=[get_composite_subobject_data(4, 0, 0, object_type="markdown")]),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    composite["object_data"]["subobjects"][0]["object_data"]["unallowed"] = "str"
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


# Run the test twice for new & existing subobjects
@pytest.mark.parametrize("subobject_id", [-1, 5])
async def test_add_incorrect_subobject_object_data_to_do_list(cli, db_cursor, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_test_object(subobject_id, owner_id=1, object_type="to_do_list", pop_keys=["object_data"])], db_cursor)
        insert_to_do_lists([get_test_object_data(subobject_id, object_type="to_do_list")], db_cursor)
    
    # Missing subobject object_data attributes (to-do list)
    for attr in ["sort_type", "items"]:
        composite = get_test_object(
            1, object_type="composite",
            object_data=get_composite_data(subobjects=[get_composite_subobject_data(7, 0, 0, object_type="to_do_list")]),
            pop_keys=["object_id", "created_at", "modified_at"]
        )
        composite["object_data"]["subobjects"][0]["object_data"].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed subobject object_data attributes (to-do list)
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(subobjects=[get_composite_subobject_data(7, 0, 0, object_type="to_do_list")]),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    composite["object_data"]["subobjects"][0]["object_data"]["unallowed"] = "str"
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_incorrect_deleted_subobjects_data(cli):
    # Missing attributes
    for attr in ["object_id", "is_full_delete"]:
        composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"])
        composite["object_data"]["deleted_subobjects"] = [{"object_id": 1, "is_full_delete": True}]
        composite["object_data"]["deleted_subobjects"][0].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Unallowed attributes
    composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"])
    composite["object_data"]["deleted_subobjects"] = [{"object_id": 1, "is_full_delete": True, "unallowed": "str"}]
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values
    incorrect_values = {"object_id": ["str", True, 0], "is_full_delete": ["str", 0]}
    for attr in incorrect_values:
        for value in incorrect_values[attr]:
            composite = get_test_object(1, object_type="composite", pop_keys=["object_id", "created_at", "modified_at"])
            composite["object_data"]["deleted_subobjects"] = [{"object_id": 1, "is_full_delete": True}]
            composite["object_data"]["deleted_subobjects"][0][attr] = value
            resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
            assert resp.status == 400


async def test_add_validation_non_unique_subobject_ids(cli):
    # Non-unique subobject ids
    composite = get_test_object(1, object_type="composite", 
                                object_data=get_composite_data(subobjects=[
                                    get_composite_subobject_data(1, 0, 0),
                                    get_composite_subobject_data(1, 0, 1)
                                ]),
                                pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_validation_missing_new_subobjects_attributes(cli):
    # New subobject without attributes/data
    for attr in ["object_name", "object_description", "object_type", "is_published", "display_in_feed", "feed_timestamp", "show_description", "object_data"]:
        composite = get_test_object(
            1, object_type="composite",
            object_data=get_composite_data(subobjects=[
                get_composite_subobject_data(-1, 0, 0, object_type="link")
            ]),
            pop_keys=["object_id", "created_at", "modified_at"]
        )
        composite["object_data"]["subobjects"][0].pop(attr)
        resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
        assert resp.status == 400


async def test_add_validation_non_existing_subobject(cli):
    # Positive subobject id, which does not exist in the database
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(subobjects=[get_composite_subobject_data(999, 0, 0)]),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_validation_non_existing_updated_subobject(cli, db_cursor):
    # Positive subobject id with updated attributes/data, which does not exist in the database
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(subobjects=[
            get_composite_subobject_data(999, 0, 0, object_type="link")
        ]),
        pop_keys=["object_id", "created_at", "modified_at"]
    )

    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400

    # Check if composite object was not added
    db_cursor.execute(f"SELECT object_id FROM objects WHERE object_type = 'composite'")
    assert not db_cursor.fetchone()
    

async def test_add_validation_incorrect_updated_subobject_type(cli, db_cursor):
    # Insert objects
    obj_list = [get_test_object(100, owner_id=1, object_type="link", pop_keys=["object_data"]),
                get_test_object(101, owner_id=1, object_type="markdown", pop_keys=["object_data"]),
                get_test_object(102, owner_id=1, object_type="to_do_list", pop_keys=["object_data"])]
    insert_objects(obj_list, db_cursor)

    # Try updating a non-existing link subobject data
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(subobjects=[get_composite_subobject_data(101, 0, 0, object_type="link")]),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400
    db_cursor.execute(f"SELECT object_id FROM objects WHERE object_type = 'composite'")
    assert not db_cursor.fetchone()

    # Try updating a non-existing Markdown subobject data
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(subobjects=[get_composite_subobject_data(100, 0, 0, object_type="markdown")]),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400
    db_cursor.execute(f"SELECT object_id FROM objects WHERE object_type = 'composite'")
    assert not db_cursor.fetchone()

    # Try updating a non-existing to-do list subobject data
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(subobjects=[get_composite_subobject_data(100, 0, 0, object_type="to_do_list")]),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400
    db_cursor.execute(f"SELECT object_id FROM objects WHERE object_type = 'composite'")
    assert not db_cursor.fetchone()


async def test_add_validation_non_unique_subobject_row_column_combinaiton(cli):
    # Non unique row + column combination
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(subobjects=[
            get_composite_subobject_data(1, 0, 0),
            get_composite_subobject_data(2, 0, 0)
        ]),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_validation_same_id_in_subobjects_and_deleted_subobjects(cli):
    # object id present both in subobjects and deleted_subobjects
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(
            subobjects=[get_composite_subobject_data(1, 0, 0)],
            deleted_subobjects=[get_deleted_subobject(999), get_deleted_subobject(1)]
        ),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


# Run the test twice for new & existing subobjects
@pytest.mark.parametrize("subobject_id", [-1, 5])
async def test_add_subobject_with_a_non_existing_owner_id(cli, db_cursor, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_object_attrs(subobject_id)], db_cursor)
        insert_links([get_test_object_data(subobject_id)], db_cursor)
    
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(
            subobjects=[get_composite_subobject_data(1, 0, 0, owner_id=1000)]
        ),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 400


# Run the test for each possible `display_mode` vlue
@pytest.mark.parametrize("display_mode", ["basic", "multicolumn", "grouped_links", "chapters"])
async def test_add_correct_object_without_subobject_updates(cli, db_cursor, display_mode):
    # Insert objects
    obj_list = [get_test_object(100 + i, owner_id=1, object_type="link", pop_keys=["object_data"]) for i in range(5)]
    insert_objects(obj_list, db_cursor)

    # Add a composite object without subobjects update
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(
            display_mode=display_mode,
            subobjects=[
                get_composite_subobject_data(100, 0, 0),
                get_composite_subobject_data(101, 0, 1),
                get_composite_subobject_data(102, 0, 2),
                get_composite_subobject_data(103, 1, 0),
                get_composite_subobject_data(104, 1, 1)
            ]
        ),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200

    # Check database state
    resp_object = (await resp.json())["object"]
    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = {resp_object['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == sorted([o["object_id"] for o in obj_list])


async def test_add_correct_object_with_new_subobjects(cli, db_cursor):
    now = datetime.now(tz=timezone.utc)
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user

    # Send request with new subobjects
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(
            subobjects=[
                get_composite_subobject_data(-1, 0, 0, object_type="link", is_published=True, display_in_feed=True, 
                                             feed_timestamp=now - timedelta(days=1), show_description=True),
                get_composite_subobject_data(-2, 0, 1, object_type="markdown", is_published=True, display_in_feed=False,
                                             feed_timestamp=now - timedelta(days=2), show_description=False),
                get_composite_subobject_data(-3, 0, 2, object_type="to_do_list", is_published=True, display_in_feed=True,
                                             feed_timestamp=now - timedelta(days=3), show_description=True),
                get_composite_subobject_data(-4, 1, 0, object_type="link", is_published=False, display_in_feed=False, show_description=False),
                get_composite_subobject_data(-5, 1, 1, object_type="markdown", is_published=False, display_in_feed=True, show_description=True),
                get_composite_subobject_data(-6, 1, 2, object_type="to_do_list", is_published=False, display_in_feed=False, show_description=False),
            ]
        ),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
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
            if int(obj_id) == so["subobject_id"]:
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
        if (expected_feed_timestamp := subobjects[object_id]["feed_timestamp"]) is None:
            assert row[6] == None
        else:
            assert datetime.fromisoformat(expected_feed_timestamp) == row[6]
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


async def test_add_correct_object_update_existing_subobjects(cli, db_cursor):
    now = datetime.now(tz=timezone.utc)
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
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(
            subobjects=[
                get_composite_subobject_data(100, 0, 0, object_type="link", object_name="updated link name",
                                             object_description="updated link descr", is_published=True, display_in_feed=True, 
                                             feed_timestamp=now - timedelta(days=1), show_description=True,
                                             object_data=get_link_data(link="https://new.link.com")),
                get_composite_subobject_data(101, 0, 1, object_type="markdown", object_name="updated markdown name",
                                             object_description="updated markdown descr", is_published=False, display_in_feed=False, 
                                             feed_timestamp=now - timedelta(days=2), show_description=False,
                                             object_data=get_markdown_data(raw_text="updated text")),
                get_composite_subobject_data(102, 0, 2, object_type="to_do_list", object_name="updated to-do list name",
                                             object_description="updated to-do list descr", is_published=True, display_in_feed=True,
                                             show_description=True, object_data=get_to_do_list_data(
                                                 items=[get_to_do_list_item_data(0, item_text="updated item text")]
                                             ))
            ]
        ),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200

    # Check if subobjects' attributes are updated
    subobjects = {so["subobject_id"]: so for so in composite["object_data"]["subobjects"]}
    db_cursor.execute(f"""SELECT object_id, object_name, object_description, object_type, is_published, display_in_feed, feed_timestamp,
        show_description, owner_id FROM objects WHERE object_id IN {tuple(subobjects.keys())}""")
    for row in db_cursor.fetchall():
        object_id = row[0]
        assert subobjects[object_id]["object_name"] == row[1]
        assert subobjects[object_id]["object_description"] == row[2]
        assert subobjects[object_id]["object_type"] == row[3]
        assert subobjects[object_id]["is_published"] == row[4]
        assert subobjects[object_id]["display_in_feed"] == row[5]
        if (expected_feed_timestamp := subobjects[object_id]["feed_timestamp"]) is None:
            assert row[6] == None
        else:
            assert datetime.fromisoformat(expected_feed_timestamp) == row[6]
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
async def test_add_correct_subobject_with_a_specified_owner_id(cli, db_cursor, owner_id, subobject_id):
    # Insert existing subobject
    if subobject_id > 0:
        insert_objects([get_object_attrs(subobject_id)], db_cursor)
        insert_links([get_test_object_data(subobject_id)], db_cursor)
    # Insert another user
    if owner_id == 2:
        insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user
    
    
    composite = get_test_object(
        1, object_type="composite",
        object_data=get_composite_data(
            subobjects=[
                get_composite_subobject_data(
                    subobject_id, 0, 0, object_type="link", object_name="subobject name", object_description="subobject descr",
                    is_published=True, show_description=True, owner_id=owner_id
                )]
        ),
        pop_keys=["object_id", "created_at", "modified_at"]
    )
    resp = await cli.post("/objects/add", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200

    mapped_subobject_id = subobject_id if subobject_id > 0 else (await resp.json())["object"]["object_data"]["id_mapping"][str(subobject_id)]
    db_cursor.execute(f"SELECT owner_id FROM objects WHERE object_id = {mapped_subobject_id}")
    assert db_cursor.fetchone() == (owner_id, )


if __name__ == "__main__":
    run_pytest_tests(__file__)
