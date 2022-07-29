import pytest

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.objects import add_composite_subobject, get_test_object, get_test_object_data, insert_composite, insert_objects
from tests.fixtures.sessions import headers_admin_token
from tests.fixtures.users import get_test_user, insert_users


async def test_incorrect_request_body_as_admin(cli):
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
        

async def test_non_existing_object_id_as_admin(cli):
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 1000}, headers=headers_admin_token)
    assert resp.status == 404


async def test_non_composite_root_object_as_admin(cli, db_cursor):
    obj_list = [get_test_object(1, owner_id=1, object_type="link", pop_keys=["object_data"])]
    insert_objects(obj_list, db_cursor)
    
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 1}, headers=headers_admin_token)
    assert resp.status == 400


async def test_correct_hierarchy_with_non_published_root_object_as_anonymous(cli, db_cursor):
    # Insert test data and get expected results
    expected_results = insert_non_cyclic_hierarchy(cli, db_cursor, root_is_published=False)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999})
    assert resp.status == 404


@pytest.mark.parametrize("headers", [None, headers_admin_token])
async def test_correct_non_cyclic_hierarchy_as_admin_and_anonymous(cli, db_cursor, headers):
    # Insert test data and get expected results
    expected_results = insert_non_cyclic_hierarchy(cli, db_cursor)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999}, headers=headers)
    assert resp.status == 200
    resp_body = await resp.json()
    assert "composite" in resp_body
    assert "non_composite" in resp_body
    assert sorted(resp_body["composite"]) == sorted(expected_results["composite"])
    assert sorted(resp_body["non_composite"]) == sorted(expected_results["non_composite"])


@pytest.mark.parametrize("headers", [None, headers_admin_token])
async def test_correct_non_cyclic_hierarchy_with_max_depth_exceeded_as_admin_and_anonymous(cli, db_cursor, headers):
    # Insert test data and get expected results
    expected_results = insert_non_cyclic_hierarchy_with_max_depth_exceeded(cli, db_cursor)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999}, headers=headers)
    assert resp.status == 200
    resp_body = await resp.json()
    assert "composite" in resp_body
    assert "non_composite" in resp_body
    assert sorted(resp_body["composite"]) == sorted(expected_results["composite"])
    assert sorted(resp_body["non_composite"]) == sorted(expected_results["non_composite"])


@pytest.mark.parametrize("headers", [None, headers_admin_token])
async def test_correct_cyclic_hierarchy_as_admin_and_anonymous(cli, db_cursor, headers):
    # Insert test data and get expected results
    expected_results = insert_a_cyclic_hierarchy(cli, db_cursor)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999}, headers=headers)
    assert resp.status == 200
    resp_body = await resp.json()
    assert "composite" in resp_body
    assert "non_composite" in resp_body
    assert sorted(resp_body["composite"]) == sorted(expected_results["composite"])
    assert sorted(resp_body["non_composite"]) == sorted(expected_results["non_composite"])


def insert_non_cyclic_hierarchy(cli, db_cursor, root_is_published = True):
    """
    Inserts a non-cyclic hierarchy for testing correct requests.

    Hierarchy structure:
    - 99999 (composite):
        - 1 (composite):
            - 11 (composite):
                - 111 (link);
                - 112 (link);
            - 12 (link);
        - 2 (composite):
            - 21 (composite, no subobjects);
            - 22 (composite):
                - 221 (link);
        - 3 (link);
        - 4 (markdown);
        - 5 (to-do list);
    """
    # `objects` table
    obj_list = [
        get_test_object(99999, owner_id=1, object_type="composite", is_published=root_is_published, pop_keys=["object_data"]),
        get_test_object(1, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(11, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(111, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(112, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(12, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(2, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(21, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(22, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(221, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(3, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(4, owner_id=1, object_type="markdown", pop_keys=["object_data"]),
        get_test_object(5, owner_id=1, object_type="to_do_list", pop_keys=["object_data"]),
    ]

    insert_objects(obj_list, db_cursor)

    # `composite` table
    composite_object_data = []

    d = get_test_object_data(99999, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1)
    add_composite_subobject(d, object_id=2)
    add_composite_subobject(d, object_id=3)
    add_composite_subobject(d, object_id=4)
    add_composite_subobject(d, object_id=5)
    composite_object_data.append(d)

    d = get_test_object_data(1, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=11)
    add_composite_subobject(d, object_id=12)
    composite_object_data.append(d)

    d = get_test_object_data(11, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=111)
    add_composite_subobject(d, object_id=112)
    composite_object_data.append(d)

    d = get_test_object_data(2, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=21)
    add_composite_subobject(d, object_id=22)
    composite_object_data.append(d)

    d = get_test_object_data(22, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=221)
    composite_object_data.append(d)

    insert_composite(composite_object_data, db_cursor)

    # Return expected results
    return {
        "composite": [99999, 1, 11, 2, 21, 22],
        "non_composite": [111, 112, 12, 221, 3, 4, 5]
    }


def insert_non_cyclic_hierarchy_with_max_depth_exceeded(cli, db_cursor):
    """
    Inserts a non-cyclic hierarchy for testing correct requests. 
    Actual hierarchy depth is bigger than the depth that should be checked by the route handler.

    Hierarchy structure:
    - 99999 (composite):
        - 1 (composite):
            - 11 (composite):
                - 111 (composite):
                    - 1111 (composite):
                        - 11111 (composite):
                            - 111111 (composite):   # expected not to be returned because of hierarchy depth limit
                                - 1111111 (link);   # expected not to be returned because of hierarchy depth limit
                                - 3 (link);
                        - 11112 (link);
                    - 1112 (link);
                - 112 (link);
            - 12 (link);
        - 2 (composite):
            - 21 (composite, no subobjects);
            - 22 (composite):
                - 221 (link);
        - 3 (link);
        - 4 (markdown);
        - 5 (to-do list);
    """
    # `objects` table
    obj_list = [
        get_test_object(99999, owner_id=1, object_type="composite", is_published=True, pop_keys=["object_data"]),
        get_test_object(1, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(11, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(111, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(1111, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(11111, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(111111, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(1111111, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(3, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(11112, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(1112, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(112, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(12, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(2, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(21, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(22, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(221, owner_id=1, object_type="link", pop_keys=["object_data"]),
        # get_test_object(3, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(4, owner_id=1, object_type="markdown", pop_keys=["object_data"]),
        get_test_object(5, owner_id=1, object_type="to_do_list", pop_keys=["object_data"]),
    ]

    insert_objects(obj_list, db_cursor)

    # `composite` table
    composite_object_data = []

    d = get_test_object_data(99999, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1)
    add_composite_subobject(d, object_id=2)
    add_composite_subobject(d, object_id=3)
    add_composite_subobject(d, object_id=4)
    add_composite_subobject(d, object_id=5)
    composite_object_data.append(d)

    d = get_test_object_data(1, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=11)
    add_composite_subobject(d, object_id=12)
    composite_object_data.append(d)

    d = get_test_object_data(11, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=111)
    add_composite_subobject(d, object_id=112)
    composite_object_data.append(d)

    d = get_test_object_data(111, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1111)
    add_composite_subobject(d, object_id=1112)
    composite_object_data.append(d)

    d = get_test_object_data(1111, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=11111)
    add_composite_subobject(d, object_id=11112)
    composite_object_data.append(d)

    d = get_test_object_data(11111, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=111111)
    composite_object_data.append(d)

    d = get_test_object_data(111111, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1111111)
    add_composite_subobject(d, object_id=3)
    composite_object_data.append(d)

    d = get_test_object_data(2, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=21)
    add_composite_subobject(d, object_id=22)
    composite_object_data.append(d)

    d = get_test_object_data(22, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=221)
    composite_object_data.append(d)

    insert_composite(composite_object_data, db_cursor)

    # Return expected results
    return {
        "composite": [99999, 1, 11, 111, 1111, 11111, 2, 21, 22],
        "non_composite": [11112, 1112, 112, 12, 221, 3, 4, 5]
    }


def insert_a_cyclic_hierarchy(cli, db_cursor):
    """
    Inserts a hierarchy with cyclic references and multiple occurence of the same composite object for testing correct requests.

    Hierarchy structure:
    - 99999 (composite):
        - 1 (composite):
            - 11 (composite):
                - 111 (composite):
                    - 1 (composite, cyclic reference);
                - 112 (link);
            - 12 (link);
        - 2 (composite):
            - 21 (composite, no subobjects);
            - 22 (composite):
                - 221 (link);
                - 21 (composite, second non-cyclic reference);
        - 3 (link);
        - 4 (markdown);
        - 5 (to-do list);
    """
    # `objects` table
    obj_list = [
        get_test_object(99999, owner_id=1, object_type="composite", is_published=True, pop_keys=["object_data"]),
        get_test_object(1, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(11, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(111, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(112, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(12, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(2, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(21, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(22, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(221, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(3, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(4, owner_id=1, object_type="markdown", pop_keys=["object_data"]),
        get_test_object(5, owner_id=1, object_type="to_do_list", pop_keys=["object_data"]),
    ]

    insert_objects(obj_list, db_cursor)

    # `composite` table
    composite_object_data = []

    d = get_test_object_data(99999, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1)
    add_composite_subobject(d, object_id=2)
    add_composite_subobject(d, object_id=3)
    add_composite_subobject(d, object_id=4)
    add_composite_subobject(d, object_id=5)
    composite_object_data.append(d)

    d = get_test_object_data(1, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=11)
    add_composite_subobject(d, object_id=12)
    composite_object_data.append(d)

    d = get_test_object_data(11, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=111)
    add_composite_subobject(d, object_id=112)
    composite_object_data.append(d)

    d = get_test_object_data(111, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1)
    composite_object_data.append(d)

    d = get_test_object_data(2, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=21)
    add_composite_subobject(d, object_id=22)
    composite_object_data.append(d)

    d = get_test_object_data(22, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=221)
    add_composite_subobject(d, object_id=21)
    composite_object_data.append(d)

    insert_composite(composite_object_data, db_cursor)

    # Return expected results
    return {
        "composite": [99999, 1, 11, 111, 2, 21, 22],
        "non_composite": [112, 12, 221, 3, 4, 5]
    }


if __name__ == "__main__":
    run_pytest_tests(__file__)
