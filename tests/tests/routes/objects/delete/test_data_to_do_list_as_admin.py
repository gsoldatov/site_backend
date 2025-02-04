"""
Tests for to-do list specific operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs, get_test_object_data
from tests.data_generators.sessions import headers_admin_token
from tests.db_operations.objects import insert_objects, insert_to_do_lists
from tests.request_generators.objects import get_objects_delete_body


async def test_delete(cli, db_cursor):
    # Insert mock values
    obj_list = [get_object_attrs(i, object_type="to_do_list") for i in range(1, 4)]
    tdl_list = [get_test_object_data(i, object_type="to_do_list") for i in range(1, 4)]
    insert_objects(obj_list, db_cursor)
    insert_to_do_lists(tdl_list, db_cursor)

    # Correct deletes (general data + to-do list)
    body = get_objects_delete_body(object_ids=[1])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM to_do_lists")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [2, 3]
    db_cursor.execute(f"SELECT DISTINCT object_id FROM to_do_list_items")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [2, 3]

    body = get_objects_delete_body(object_ids=[2, 3])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM to_do_lists")
    assert not db_cursor.fetchone()
    db_cursor.execute(f"SELECT DISTINCT object_id FROM to_do_list_items")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
