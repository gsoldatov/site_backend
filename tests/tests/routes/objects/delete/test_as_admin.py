import json

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.sessions import headers_admin_token
from tests.data_sets.objects import insert_data_for_delete_tests
from tests.request_generators.objects import get_objects_delete_body


async def test_incorrect_request_body(cli):
    # Invalid JSON
    resp = await cli.delete("/objects/delete", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Missing attributes
    for attr in ("object_ids", "delete_subobjects"):
        body = get_objects_delete_body()
        body.pop(attr)
        resp = await cli.delete("/objects/delete", data=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attributes values
    incorrect_attributes = {
        "object_ids": [None, 1, "a", False, {}, ["a"], [-1], [0], [1] * 1001],
        "delete_subobjects": [None, 2, "a", {}, []]
    }
    for attr, values in incorrect_attributes.items():
        for value in values:
            body = get_objects_delete_body()
            body[attr] = value
            resp = await cli.delete("/objects/delete", data=body, headers=headers_admin_token)
            assert resp.status == 400


async def test_delete_non_existing_objects(cli, db_cursor):
    insert_data_for_delete_tests(db_cursor)

    body = get_objects_delete_body(object_ids=[1000, 2000])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
    assert resp.status == 200


async def test_delete_objects(cli, db_cursor):
    insert_data_for_delete_tests(db_cursor)

    # Correct deletes (general data + link)
    body = get_objects_delete_body(object_ids=[1])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM objects")
    assert db_cursor.fetchone() == (2,)
    assert db_cursor.fetchone() == (3,)
    assert not db_cursor.fetchone()

    body = get_objects_delete_body(object_ids=[2, 3])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM objects")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
