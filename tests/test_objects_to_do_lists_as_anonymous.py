"""
Tests for operations with to-do lists performed as anonymous.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))
    from tests.util import run_pytest_tests


from util import check_ids
from fixtures.objects import insert_data_for_view_objects_as_anonymous


async def test_view(cli, db_cursor):
    insert_data_for_view_objects_as_anonymous(cli, db_cursor, object_type="to_do_list")

    # Correct request (object_data_ids only, to-do lists, request all existing objects, receive only published)
    requested_object_ids = [i for i in range(1, 11)]
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]
    resp = await cli.post("/objects/view", json={"object_data_ids": requested_object_ids})
    assert resp.status == 200
    data = await resp.json()

    check_ids(expected_object_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as anonymous, to-do lists object_data_ids only")


if __name__ == "__main__":
    run_pytest_tests(__file__)
