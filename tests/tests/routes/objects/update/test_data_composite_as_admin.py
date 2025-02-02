"""
Tests for composite objects' data operations performed as admin.
"""
import pytest

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_object_attrs, get_composite_data, \
    get_composite_subobject_data, get_deleted_subobject
from tests.data_generators.sessions import headers_admin_token

from tests.db_operations.objects import insert_objects, insert_composite


# Update handler uses the same logic as add handler, so tests are not duplicated
async def test_update_correct_object_without_subobject_updates(cli, db_cursor):
    """Update composite subobject without updating its subobjects data"""
    # Insert objects
    obj_list = [get_object_attrs(100 + i, object_type="link") for i in range(5)]
    obj_list.append(get_object_attrs(1, object_type="composite"))
    insert_objects(obj_list, db_cursor)

    # Insert existing composite object data
    composite_data = get_composite_data(subobjects=[
        get_composite_subobject_data(100, 0, 0),
        get_composite_subobject_data(101, 0, 1)
    ])
    insert_composite([{"object_id": 1, "object_data": composite_data}], db_cursor)

    # Update a composite object without subobjects update
    composite = get_test_object(
        1, object_type="composite", 
        object_data=get_composite_data(subobjects=composite_data["subobjects"] + [
            get_composite_subobject_data(102, 0, 2),
            get_composite_subobject_data(103, 1, 0),
            get_composite_subobject_data(104, 1, 1)
        ]),
        pop_keys=["object_type", "created_at", "modified_at"])

    resp = await cli.put("/objects/update", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200

    # Check database state
    resp_object = (await resp.json())["object"]
    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = {resp_object['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == sorted([so["subobject_id"] for so in composite["object_data"]["subobjects"]])


# Run the test for each possible `display_mode` vlue
@pytest.mark.parametrize("display_mode", ["basic", "multicolumn", "grouped_links", "chapters"])
async def test_update_correct_object_with_subobject_full_and_not_full_delete(cli, db_cursor, display_mode):
    # Insert objects
    obj_list = [get_test_object(100 + i, owner_id=1, object_type="link", pop_keys=["object_data"]) for i in range(4)]   # 4 subobjects
    obj_list.extend([get_test_object(10 + i, owner_id=1, object_type="composite", pop_keys=["object_data"]) for i in range(2)]) # 2 composite objects
    insert_objects(obj_list, db_cursor)

    # Insert composite data (10: 100, 101, 102, 103; 11: 103)
    composite_data = get_composite_data(
        subobjects=[get_composite_subobject_data(100 + i, 0, i - 1) for i in range(1, 4)]
    )
    insert_composite([{"object_id": 10, "object_data": composite_data}], db_cursor)

    composite_data = get_composite_data(subobjects=[get_composite_subobject_data(103, 0, 0)])
    insert_composite([{"object_id": 11, "object_data": composite_data}], db_cursor)

    # Update first composite object (1 subobject remain & 2 subobjects are marked as fully deleted (one is present in the second object))
    composite = get_test_object(
        10, object_type="composite",
        object_data=get_composite_data(
            subobjects=[get_composite_subobject_data(100, 0, 0)],
            deleted_subobjects=[get_deleted_subobject(101, is_full_delete=False), get_deleted_subobject(102), get_deleted_subobject(103)]
        ),
        pop_keys=["object_type", "created_at", "modified_at"]
    )
    resp = await cli.put("/objects/update", json={"object": composite}, headers=headers_admin_token)
    assert resp.status == 200

    # Check database
    db_cursor.execute(f"SELECT object_id FROM objects")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [10, 11, 100, 101, 103]  # 102 and 103 were marked for full deletion; 103 was not deleted, 
                                                                                    # because it's still a subobject of 11;
                                                                                    # 101 was deleted without full deletion and, thus, remains in the database
    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = 10")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [100]    # 101 was deleted; 102 and 103 were fully deleted

    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = 11")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [103]    # subobjects of 11 are not changed


if __name__ == "__main__":
    run_pytest_tests(__file__)
