"""
Tests for link-specific operations performed as anonymous.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))
    from tests.util import run_pytest_tests


from util import check_ids
from fixtures.objects import insert_data_for_view_tests_non_published_objects, insert_data_for_view_tests_objects_with_non_published_tags


async def test_view_non_published_objects(cli, db_cursor):
    insert_data_for_view_tests_non_published_objects(db_cursor, object_type="link")

    # Correct request (object_data_ids only, links, request all existing objects, receive only published)
    requested_object_ids = [i for i in range(1, 11)]
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]
    resp = await cli.post("/objects/view", json={"object_data_ids": requested_object_ids})
    assert resp.status == 200
    data = await resp.json()

    check_ids(expected_object_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as anonymous, link object_data_ids only")


async def test_view_objects_with_non_published_tags(cli, db_cursor):
    # Insert data (published objects with published & non-published tags)
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor, object_type="link")
    requested_object_ids = inserts["inserted_object_ids"]
    expected_object_ids = inserts["expected_object_ids_as_anonymous"]

    # Correct request (object_ids only)
    resp = await cli.post("/objects/view", json={"object_data_ids": requested_object_ids})
    assert resp.status == 200
    data = await resp.json()
    check_ids(expected_object_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as anonymous, link object_data_ids only")


if __name__ == "__main__":
    run_pytest_tests(__file__)
