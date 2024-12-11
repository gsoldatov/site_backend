"""
Tests for composite objects' data operations performed as anonymous.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.objects import get_test_object, get_test_object_data
from tests.fixtures.data_generators.users import get_test_user

from tests.fixtures.data_sets.objects import insert_data_for_composite_view_tests_objects_with_non_published_tags

from tests.fixtures.db_operations.objects import insert_objects, insert_composite
from tests.fixtures.db_operations.users import insert_users

from tests.util import ensure_equal_collection_elements


async def test_view_non_published_composite(cli, db_cursor):
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user
    object_attributes = [get_test_object(1, owner_id=1, pop_keys=["object_data"])]
    object_attributes.extend([get_test_object(i, object_type="composite", is_published=i % 2 == 0,
        owner_id=1 if i <= 35 else 2, pop_keys=["object_data"]) for i in range(31, 41)])
    insert_objects(object_attributes, db_cursor)
    composite_object_data = [get_test_object_data(i, object_type="composite") for i in range(31, 41)]
    insert_composite(composite_object_data, db_cursor)

    # Correct request (object_data_ids only, composite, request all composite objects, receive only published)
    requested_object_ids = [i for i in range(31, 41)]
    expected_object_ids = [i for i in range(31, 41) if i % 2 == 0]
    resp = await cli.post("/objects/view", json={"object_data_ids": requested_object_ids})
    assert resp.status == 200
    data = await resp.json()

    ensure_equal_collection_elements(expected_object_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as anonymous, composite object_data_ids only")


async def test_view_composite_with_at_least_one_non_published_tag(cli, db_cursor):
    # Insert data
    insert_data_for_composite_view_tests_objects_with_non_published_tags(db_cursor)

    # Correct request (object_data_ids only, composite, request all composite objects, receive only marked with published tags)
    resp = await cli.post("/objects/view", json={"object_data_ids": [11, 12, 13]})
    assert resp.status == 200
    data = await resp.json()

    ensure_equal_collection_elements([11], [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as anonymous, composite object_data_ids only")


if __name__ == "__main__":
    run_pytest_tests(__file__)
