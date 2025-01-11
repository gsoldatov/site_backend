if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_sets.objects import insert_data_for_view_tests_non_published_objects, \
    insert_data_for_view_tests_objects_with_non_published_tags
from tests.request_generators.objects import get_objects_search_request_body


async def test_correct_search_non_published_objects(cli, db_cursor):
    insert_data_for_view_tests_non_published_objects(db_cursor)
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]

    # Search a pattern matching all existing objects (and receive only published in the response)
    body = get_objects_search_request_body()
    resp = await cli.post("/objects/search", json=body)
    assert resp.status == 200
    data = await resp.json()
    assert sorted(data["object_ids"]) == expected_object_ids


async def test_correct_search_objects_with_non_published_tags(cli, db_cursor):
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor)
    expected_object_ids = inserts["expected_object_ids_as_anonymous"]

    # Search a pattern matching all existing objects (and receive only published in the response)
    body = get_objects_search_request_body()
    resp = await cli.post("/objects/search", json=body)
    assert resp.status == 200
    data = await resp.json()
    assert sorted(data["object_ids"]) == expected_object_ids


if __name__ == "__main__":
    run_pytest_tests(__file__)
