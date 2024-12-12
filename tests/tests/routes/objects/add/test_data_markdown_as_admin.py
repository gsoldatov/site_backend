"""
Tests for markdown-specific operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.objects import get_test_object
from tests.fixtures.data_generators.sessions import headers_admin_token


async def test_add(cli, db_cursor):
    # Incorrect markdown attributes
    for attr in [{"incorrect MD attr": "123"}, {"incorrect MD attr": "123", "raw_text": "New text"}]:
        md = get_test_object(1, object_type="markdown", pop_keys=["object_id", "created_at", "modified_at"])
        md["object_data"] = attr
        resp = await cli.post("/objects/add", json={"object": md}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect markdown value
    md = get_test_object(1, object_type="markdown", pop_keys=["object_id", "created_at", "modified_at"])
    md["object_data"] = {"raw_text": ""}
    resp = await cli.post("/objects/add", json={"object": md}, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute(f"SELECT object_name FROM objects") # Check that a new object was not created
    assert not db_cursor.fetchone()
    db_cursor.execute(f"SELECT raw_text FROM markdown")
    assert not db_cursor.fetchone()

    # Add a correct markdown object
    md = get_test_object(1, object_type="markdown", pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": md}, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert "object" in resp_json
    resp_object = resp_json["object"]

    db_cursor.execute(f"SELECT raw_text FROM markdown WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (md["object_data"]["raw_text"],)


if __name__ == "__main__":
    run_pytest_tests(__file__)
