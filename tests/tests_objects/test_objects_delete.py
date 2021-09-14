import json

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.fixtures.objects import get_test_object, get_test_object_data, insert_objects, insert_links
from tests.fixtures.sessions import headers_admin_token


async def test_incorrect_request_body_as_admin(cli):
    # Incorrect attributes and values
    for value in ["123", {"incorrect_key": "incorrect_value"}, {"object_ids": "incorrect_value"}, {"object_ids": []}]:
        body = value if type(value) == str else json.dumps(value)
        resp = await cli.delete("/objects/delete", data=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_delete_non_existing_objects_as_admin(cli, db_cursor):
    _insert_mock_data_for_delete_tests(cli, db_cursor)

    resp = await cli.delete("/objects/delete", json={"object_ids": [1000, 2000]}, headers=headers_admin_token)
    assert resp.status == 404


async def test_delete_objects_as_admin(cli, db_cursor):
    _insert_mock_data_for_delete_tests(cli, db_cursor)

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


async def test_delete_objects_as_anonymous(cli, db_cursor):
    _insert_mock_data_for_delete_tests(cli, db_cursor)

    # Correct deletes (general data + link)
    resp = await cli.delete("/objects/delete", json={"object_ids": [2, 3]})
    assert resp.status == 401
    db_cursor.execute(f"SELECT count(*) FROM objects")
    assert db_cursor.fetchone()[0] == 3


def _insert_mock_data_for_delete_tests(cli, db_cursor):
    obj_list = [get_test_object(1, owner_id=1, pop_keys=["object_data"]), get_test_object(2, owner_id=1, pop_keys=["object_data"]),
        get_test_object(3, owner_id=1, pop_keys=["object_data"])]
    l_list = [get_test_object_data(1), get_test_object_data(2), get_test_object_data(3)]
    insert_objects(obj_list, db_cursor,)
    insert_links(l_list, db_cursor)


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
