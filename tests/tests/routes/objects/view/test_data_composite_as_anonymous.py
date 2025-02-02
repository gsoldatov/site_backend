"""
Tests for composite objects' data operations performed as anonymous.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs, get_test_object_data
from tests.data_generators.users import get_test_user

from tests.data_sets.objects import insert_data_for_composite_view_tests_objects_with_non_published_tags

from tests.db_operations.objects import insert_objects, insert_composite
from tests.db_operations.users import insert_users

from tests.request_generators.objects import get_objects_view_request_body


async def test_view_non_published_composite(cli, db_cursor):
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user
    object_attributes = [get_object_attrs(1)]
    object_attributes.extend([get_object_attrs(i, object_type="composite", is_published=i % 2 == 0,
        owner_id=1 if i <= 35 else 2) for i in range(31, 41)])
    insert_objects(object_attributes, db_cursor)
    composite_object_data = [get_test_object_data(i, object_type="composite") for i in range(31, 41)]
    insert_composite(composite_object_data, db_cursor)

    # Check if data is returned for published objects only
    requested_object_ids = [i for i in range(31, 41)]
    expected_object_ids = [i for i in range(31, 41) if i % 2 == 0]
    body = get_objects_view_request_body(object_ids=[], object_data_ids=requested_object_ids)
    resp = await cli.post("/objects/view", json=body)
    assert resp.status == 200
    data = await resp.json()

    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    assert sorted(expected_object_ids) == sorted(received_objects_data_ids)


async def test_view_composite_with_at_least_one_non_published_tag(cli, db_cursor):
    # Insert data
    insert_data_for_composite_view_tests_objects_with_non_published_tags(db_cursor)

    # Check if data is returned for objects with published tags only
    body = get_objects_view_request_body(object_ids=[], object_data_ids=[11, 12, 13])
    resp = await cli.post("/objects/view", json=body)
    assert resp.status == 200
    data = await resp.json()

    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    assert sorted([11]) == sorted(received_objects_data_ids)


if __name__ == "__main__":
    run_pytest_tests(__file__)
