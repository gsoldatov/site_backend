if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.objects import insert_data_for_view_objects_as_anonymous


async def test_correct_search_request(cli, db_cursor):
    insert_data_for_view_objects_as_anonymous(cli, db_cursor)
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]

    # Search a pattern matching all existing objects (and receive only published in the response)
    req_body = {"query": {"query_text": "object", "maximum_values": 10}}
    resp = await cli.post("/objects/search", json=req_body)
    assert resp.status == 200
    data = await resp.json()
    assert sorted(data["object_ids"]) == expected_object_ids


if __name__ == "__main__":
    run_pytest_tests(__file__)
