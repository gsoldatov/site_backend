import json

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.sessions import headers_admin_token

from tests.fixtures.data_sets.objects import insert_data_for_delete_tests


async def test_incorrect_request_body(cli):
    # Incorrect attributes and values
    for value in ["123", {"incorrect_key": "incorrect_value"}, {"object_ids": "incorrect_value"}, {"object_ids": []}]:
        body = value if type(value) == str else json.dumps(value)
        resp = await cli.delete("/objects/delete", data=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_delete_non_existing_objects(cli, db_cursor):
    insert_data_for_delete_tests(db_cursor)

    resp = await cli.delete("/objects/delete", json={"object_ids": [1000, 2000]}, headers=headers_admin_token)
    assert resp.status == 404


async def test_delete_objects(cli, db_cursor):
    insert_data_for_delete_tests(db_cursor)

    # Correct deletes (general data + link)
    resp = await cli.delete("/objects/delete", json={"object_ids": [1]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM objects")
    assert db_cursor.fetchone() == (2,)
    assert db_cursor.fetchone() == (3,)
    assert not db_cursor.fetchone()

    resp = await cli.delete("/objects/delete", json={"object_ids": [2, 3]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM objects")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
