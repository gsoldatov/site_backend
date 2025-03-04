"""
Tests for composite objects' data operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs, get_composite_data, get_composite_subobject_data
from tests.data_generators.sessions import headers_admin_token
from tests.db_operations.objects import insert_objects, insert_composite
from tests.request_generators.objects import get_objects_delete_body


async def test_delete_composite(cli, db_cursor):
    # Insert mock objects (composite: 10, 11; links: 101, 102, 103)
    obj_list = [get_object_attrs(100 + i, object_type="link") for i in range(1, 4)]   # 3 subobjects
    obj_list.extend([get_object_attrs(10 + i, object_type="composite") for i in range(2)]) # 2 composite objects
    insert_objects(obj_list, db_cursor)

    # Insert composite data (10: 101, 102, 103; 11: 103)
    composite_data = get_composite_data(
        subobjects=[get_composite_subobject_data(100 + i, 0, i - 1) for i in range(1, 4)]
    )
    insert_composite([{"object_id": 10, "object_data": composite_data}], db_cursor)

    composite_data = get_composite_data(subobjects=[get_composite_subobject_data(103, 0, 0)])
    insert_composite([{"object_id": 11, "object_data": composite_data}], db_cursor)

    # Delete composite
    body = get_objects_delete_body(object_ids=[10])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
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
    obj_list = [get_object_attrs(100 + i, object_type="link") for i in range(4)]   # 1 non-subobject + 3 subobjects
    obj_list.extend([get_object_attrs(10 + i, object_type="composite") for i in range(2)]) # 2 composite objects
    insert_objects(obj_list, db_cursor)

    # Insert composite data (10: 101, 102, 103; 11: 103)
    composite_data = get_composite_data(
        subobjects=[get_composite_subobject_data(100 + i, 0, i - 1) for i in range(1, 4)]
    )
    insert_composite([{"object_id": 10, "object_data": composite_data}], db_cursor)

    composite_data = get_composite_data(subobjects=[get_composite_subobject_data(103, 0, 0)])
    insert_composite([{"object_id": 11, "object_data": composite_data}], db_cursor)

    # Delete with subobjects: first composite (10), 1 non-subobject link (100) and 1 of its exclusive subobjects (101)
    body = get_objects_delete_body(object_ids=[10, 100, 101], delete_subobjects=True)
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
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
