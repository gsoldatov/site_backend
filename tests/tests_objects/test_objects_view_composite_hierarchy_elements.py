if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.objects import get_test_object, insert_objects, insert_non_cyclic_hierarchy, \
    insert_non_cyclic_hierarchy_with_max_depth_exceeded, insert_a_cyclic_hierarchy
from tests.fixtures.sessions import headers_admin_token


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.post("/objects/view_composite_hierarchy_elements", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400
    
    # Required attributes missing
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={}, headers=headers_admin_token)
    assert resp.status == 400

    # Unallowed attributes
    body = {"object_id": 1, "unallowed": "unallowed"}
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values for general attributes
    for k, v in [("object_id", "str"), ("object_id", True), ("object_id", [1]), ("object_id", 0)]:
        body = {"object_id": 1} # Correct request body
        body[k] = v
        resp = await cli.post("/objects/view_composite_hierarchy_elements", json=body, headers=headers_admin_token)
        assert resp.status == 400
        

async def test_non_existing_object_id(cli):
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 1000}, headers=headers_admin_token)
    assert resp.status == 404


async def test_non_composite_root_object(cli, db_cursor):
    obj_list = [get_test_object(1, owner_id=1, object_type="link", pop_keys=["object_data"])]
    insert_objects(obj_list, db_cursor)
    
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 1}, headers=headers_admin_token)
    assert resp.status == 400


async def test_correct_hierarchy_with_non_published_root_object(cli, db_cursor):
    # Insert test data and get expected results
    expected_results = insert_non_cyclic_hierarchy(db_cursor, root_is_published=False)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999})
    assert resp.status == 404


async def test_correct_non_cyclic_hierarchy(cli, db_cursor):
    # Insert test data and get expected results
    expected_results = insert_non_cyclic_hierarchy(db_cursor)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999}, headers=headers_admin_token)
    assert resp.status == 200
    resp_body = await resp.json()
    assert "composite" in resp_body
    assert "non_composite" in resp_body
    assert sorted(resp_body["composite"]) == sorted(expected_results["composite"])
    assert sorted(resp_body["non_composite"]) == sorted(expected_results["non_composite"])


async def test_correct_non_cyclic_hierarchy_with_max_depth_exceeded(cli, db_cursor):
    # Insert test data and get expected results
    expected_results = insert_non_cyclic_hierarchy_with_max_depth_exceeded(db_cursor)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999}, headers=headers_admin_token)
    assert resp.status == 200
    resp_body = await resp.json()
    assert "composite" in resp_body
    assert "non_composite" in resp_body
    assert sorted(resp_body["composite"]) == sorted(expected_results["composite"])
    assert sorted(resp_body["non_composite"]) == sorted(expected_results["non_composite"])


async def test_correct_cyclic_hierarchy(cli, db_cursor):
    # Insert test data and get expected results
    expected_results = insert_a_cyclic_hierarchy(db_cursor)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999}, headers=headers_admin_token)
    assert resp.status == 200
    resp_body = await resp.json()
    assert "composite" in resp_body
    assert "non_composite" in resp_body
    assert sorted(resp_body["composite"]) == sorted(expected_results["composite"])
    assert sorted(resp_body["non_composite"]) == sorted(expected_results["non_composite"])


if __name__ == "__main__":
    run_pytest_tests(__file__)
