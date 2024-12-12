if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_sets.objects import insert_non_cyclic_hierarchy, \
    insert_non_cyclic_hierarchy_with_max_depth_exceeded, insert_a_cyclic_hierarchy


async def test_correct_hierarchy_with_non_published_root_object(cli, db_cursor):
    # Insert test data and get expected results
    expected_results = insert_non_cyclic_hierarchy(db_cursor, root_is_published=False)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999})
    assert resp.status == 404


async def test_correct_hierarchy_with_root_object_with_non_published_tag(cli, db_cursor):
    # Insert test data and get expected results
    expected_results = insert_non_cyclic_hierarchy(db_cursor, root_has_non_published_tag=True)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999})
    assert resp.status == 404


async def test_correct_non_cyclic_hierarchy(cli, db_cursor):
    # Insert test data and get expected results
    expected_results = insert_non_cyclic_hierarchy(db_cursor)

    # Get response and check it
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999})
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
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999})
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
    resp = await cli.post("/objects/view_composite_hierarchy_elements", json={"object_id": 99999})
    assert resp.status == 200
    resp_body = await resp.json()
    assert "composite" in resp_body
    assert "non_composite" in resp_body
    assert sorted(resp_body["composite"]) == sorted(expected_results["composite"])
    assert sorted(resp_body["non_composite"]) == sorted(expected_results["non_composite"])


if __name__ == "__main__":
    run_pytest_tests(__file__)
