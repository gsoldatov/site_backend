if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.fixtures.objects import get_test_object, get_test_object_data, incorrect_object_values, insert_objects, insert_links
from tests.fixtures.users import headers_admin_token


async def test_incorrect_request_body_as_admin(cli):
    # Incorrect request body
    resp = await cli.put("/objects/update", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for payload in ({}, {"test": "wrong attribute"}, {"object": "wrong value type"}):
        resp = await cli.put("/objects/update", json=payload, headers=headers_admin_token)
        assert resp.status == 400
    
    # Missing attributes
    for attr in ("object_id", "object_name", "object_description"):
        obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
        obj.pop(attr)
        resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute types and lengths:
    for k, v in incorrect_object_values:
        if k != "object_type":
            obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
            obj[k] = v
            resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
            assert resp.status == 400


async def test_update_with_incorrect_data_as_admin(cli, db_cursor, config):
    # Insert mock values
    _insert_mock_data_for_update_tests(cli, db_cursor, config)
        
    # Non-existing object_id
    obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 100
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 400


async def test_update_with_duplicate_names_as_admin(cli, db_cursor, config):
    # Insert mock values
    _insert_mock_data_for_update_tests(cli, db_cursor, config)

    # Duplicate object_name
    obj = get_test_object(2, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    # Lowercase duplicate object_name
    obj = get_test_object(2, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    obj["object_name"] = obj["object_name"].upper()
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200


async def test_correct_update_as_admin(cli, db_cursor, config):
    objects = config["db"]["db_schema"] + ".objects"

    # Insert mock values
    _insert_mock_data_for_update_tests(cli, db_cursor, config)

    # Correct update (general attributes)
    obj = get_test_object(3, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_name FROM {objects} WHERE object_id = 1")
    assert db_cursor.fetchone() == (obj["object_name"],)


async def test_correct_update_as_anonymous(cli, db_cursor, config):
    objects = config["db"]["db_schema"] + ".objects"

    # Insert mock values
    _insert_mock_data_for_update_tests(cli, db_cursor, config)

    # Correct update (general attributes)
    obj = get_test_object(3, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json={"object": obj})
    assert resp.status == 401
    db_cursor.execute(f"SELECT object_name FROM {objects} WHERE object_id = 1")
    assert db_cursor.fetchone() != (obj["object_name"],)


def _insert_mock_data_for_update_tests(cli, db_cursor, config):
    objects = config["db"]["db_schema"] + ".objects"
    links = config["db"]["db_schema"] + ".links"
    obj_list = [get_test_object(1, owner_id=1, pop_keys=["object_data"]), get_test_object(2, owner_id=1, pop_keys=["object_data"])]
    l_list = [get_test_object_data(1), get_test_object_data(2)]
    insert_objects(obj_list, db_cursor, config)
    insert_links(l_list, db_cursor, config)


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
