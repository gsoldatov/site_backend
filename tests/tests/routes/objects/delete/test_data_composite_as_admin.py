"""
Tests for composite objects' data operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.objects import get_test_object, get_test_object_data, add_composite_subobject
from tests.fixtures.data_generators.sessions import headers_admin_token

from tests.fixtures.db_operations.objects import insert_objects, insert_composite


async def test_delete_composite(cli, db_cursor):
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


async def test_delete_with_subobjects(cli, db_cursor):
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
    run_pytest_tests(__file__)
