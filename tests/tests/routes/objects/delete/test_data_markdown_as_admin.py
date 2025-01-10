"""
Tests for markdown-specific operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_test_object_data
from tests.data_generators.sessions import headers_admin_token
from tests.db_operations.objects import insert_objects, insert_markdown
from tests.request_generators.objects import get_objects_delete_body


async def test_delete(cli, db_cursor):
    # Insert mock values
    obj_list = [get_test_object(1, object_type="markdown", owner_id=1, pop_keys=["object_data"]), 
                get_test_object(2, object_type="markdown", owner_id=1, pop_keys=["object_data"]),
                get_test_object(3, object_type="markdown", owner_id=1, pop_keys=["object_data"])]
    md_list = [get_test_object_data(1, object_type="markdown"), get_test_object_data(2, object_type="markdown"), 
               get_test_object_data(3, object_type="markdown")]
    insert_objects(obj_list, db_cursor)
    insert_markdown(md_list, db_cursor)

    # Correct deletes (general data + markdown)
    body = get_objects_delete_body(object_ids=[1])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM markdown")
    assert db_cursor.fetchone() == (2,)
    assert db_cursor.fetchone() == (3,)
    assert not db_cursor.fetchone()

    body = get_objects_delete_body(object_ids=[2, 3])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM markdown")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
