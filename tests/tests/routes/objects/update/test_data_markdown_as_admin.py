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


async def test_update(cli, db_cursor):
    # Insert mock values
    obj_list = [get_test_object(1, object_type="markdown", owner_id=1, pop_keys=["object_data"]), 
                get_test_object(2, object_type="markdown", owner_id=1, pop_keys=["object_data"])]
    md_list = [get_test_object_data(1, object_type="markdown"), get_test_object_data(2, object_type="markdown")]
    insert_objects(obj_list, db_cursor)
    insert_markdown(md_list, db_cursor)

    # Incorrect attributes in object_data for markdown
    for object_data in [{}, {"raw_text": "Some text", "incorrect_attr": 1}, {"raw_text": ""}, {"raw_text": 123}]:
        obj = get_test_object(3, object_type="markdown", pop_keys=["created_at", "modified_at", "object_type"])
        obj["object_id"] = 1
        obj["object_data"] = object_data
        resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 400

    # Correct update (markdown)
    obj = get_test_object(3, object_type="markdown", pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT raw_text FROM markdown WHERE object_id = 1")
    assert db_cursor.fetchone() == (obj["object_data"]["raw_text"],)


if __name__ == "__main__":
    run_pytest_tests(__file__)
