if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.objects import get_test_object
from tests.fixtures.data_generators.sessions import headers_admin_token

from tests.fixtures.data_sets.objects import incorrect_object_values, insert_data_for_update_tests


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.put("/objects/update", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for payload in ({}, {"test": "wrong attribute"}, {"object": "wrong value type"}):
        resp = await cli.put("/objects/update", json=payload, headers=headers_admin_token)
        assert resp.status == 400
    
    # Missing attributes
    for attr in ("object_id", "object_name", "object_description", "is_published", "display_in_feed", "feed_timestamp", "show_description"):
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


async def test_update_with_incorrect_data(cli, db_cursor):
    # Insert mock values
    insert_data_for_update_tests(db_cursor)
        
    # Non-existing object_id
    obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 100
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 400

    # Non-existing owner_id
    obj = get_test_object(1, owner_id=1000, pop_keys=["created_at", "modified_at", "object_type"])
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 400


if __name__ == "__main__":
    run_pytest_tests(__file__)
