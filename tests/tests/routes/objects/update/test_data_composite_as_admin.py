"""
Tests for composite objects' data operations performed as admin.
"""
import pytest

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.objects import get_test_object, get_test_object_data, add_composite_subobject
from tests.fixtures.data_generators.sessions import headers_admin_token

from tests.fixtures.db_operations.objects import insert_objects, insert_composite


# Update handler uses the same logic as add handler, so tests are not duplicated
async def test_update_correct_object_without_subobject_updates(cli, db_cursor):
    """Update composite subobject without updating its subobjects data"""
    # Insert objects
    obj_list = [get_test_object(100 + i, owner_id=1, object_type="link", pop_keys=["object_data"]) for i in range(5)]
    obj_list.append(get_test_object(1, object_type="composite", owner_id=1, pop_keys=["object_data"]))
    insert_objects(obj_list, db_cursor)

    # Insert existing composite object data
    composite_data = get_test_object_data(1, object_type="composite")
    composite_data["object_data"]["subobjects"] = []
    add_composite_subobject(composite_data, object_id=100)
    add_composite_subobject(composite_data, object_id=101)
    insert_composite([composite_data], db_cursor)

    # Update a composite object without subobjects update
    composite = get_test_object(1, object_type="composite", pop_keys=["object_type", "created_at", "modified_at"])
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


# Run the test for each possible `display_mode` vlue
@pytest.mark.parametrize("display_mode", ["basic", "multicolumn", "grouped_links", "chapters"])
async def test_update_correct_object_with_subobject_full_and_not_full_delete(cli, db_cursor, display_mode):
    # Insert objects
    obj_list = [get_test_object(100 + i, owner_id=1, object_type="link", pop_keys=["object_data"]) for i in range(4)]   # 4 subobjects
    obj_list.extend([get_test_object(10 + i, owner_id=1, object_type="composite", pop_keys=["object_data"]) for i in range(2)]) # 2 composite objects
    insert_objects(obj_list, db_cursor)

    # Insert composite data (10: 100, 101, 102, 103; 11: 103)
    composite_data = get_test_object_data(10, object_type="composite")
    composite_data["object_data"]["subobjects"] = []
    composite_data["object_data"]["display_mode"] = display_mode
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


if __name__ == "__main__":
    run_pytest_tests(__file__)
