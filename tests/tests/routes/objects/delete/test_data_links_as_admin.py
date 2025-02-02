"""
Tests for link-specific operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs, get_test_object_data
from tests.data_generators.sessions import headers_admin_token
from tests.db_operations.objects import insert_objects, insert_links
from tests.request_generators.objects import get_objects_delete_body


async def test_delete(cli, db_cursor):
    # Insert mock values
    obj_list = [get_object_attrs(i) for i in range(1, 4)]
    l_list = [get_test_object_data(i) for i in range(1, 4)]
    insert_objects(obj_list, db_cursor)
    insert_links(l_list, db_cursor)

    # Correct deletes (general data + link)
    body = get_objects_delete_body(object_ids=[1])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM links")
    assert db_cursor.fetchone() == (2,)
    assert db_cursor.fetchone() == (3,)
    assert not db_cursor.fetchone()

    body = get_objects_delete_body(object_ids=[2, 3])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM links")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
