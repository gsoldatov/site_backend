from datetime import datetime

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.sessions import headers_admin_token

from tests.fixtures.data_sets.objects import insert_data_for_view_tests_non_published_objects, insert_data_for_view_tests_objects_with_non_published_tags

from tests.util import check_ids


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.post("/objects/view", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for payload in [{}, {"object_ids": []}, {"object_ids": [1, -1]}, {"object_ids": [1, "abc"]},
                        {"object_data_ids": []}, {"object_data_ids": [1, -1]}, {"object_data_ids": [1, "abc"]},
                        {"object_ids": [1], "object_data_ids": [-1]}, {"object_ids": [-1], "object_data_ids": [1]}]:
        resp = await cli.post("/objects/view", json=payload, headers=headers_admin_token)
        assert resp.status == 400


async def test_view_non_existing_objects(cli):
    for key in {"object_ids", "object_data_ids"}:
        resp = await cli.post("/objects/view", json={key: [999, 1000]}, headers=headers_admin_token)
        assert resp.status == 404


async def test_view_non_published_objects(cli, db_cursor):
    # Insert mock values
    inserts = insert_data_for_view_tests_non_published_objects(db_cursor)
    obj_list = inserts["object_attributes"]
    expected_object_ids = inserts["inserted_object_ids"]
    
    # Correct request (object_ids only)
    resp = await cli.post("/objects/view", json={"object_ids": expected_object_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "objects" in data

    for field in ("object_id", "object_type", "object_name", "object_description", "created_at", "modified_at", "is_published", "display_in_feed", "feed_timestamp", "show_description"):
        assert field in data["objects"][0]

    check_ids(expected_object_ids, [data["objects"][x]["object_id"] for x in range(len(data["objects"]))], 
        "Objects view, correct request as admin, object_ids only")

    mock_feed_timestamps = list(map(lambda o: o["feed_timestamp"], sorted(obj_list, key=lambda o: o["object_id"])))
    response_feed_timestamps = list(map(lambda o: o["feed_timestamp"], sorted(data["objects"], key=lambda o: o["object_id"])))

    for i in range(len(mock_feed_timestamps)):  # Check empty & non-empty `feed_timestamp` values
        if mock_feed_timestamps[i] == "": assert response_feed_timestamps[i] == ""
        else: assert datetime.fromisoformat(mock_feed_timestamps[i]) == datetime.fromisoformat(response_feed_timestamps[i])
    
    # NOTE: object_data_ids only case is checked type-specific tests

    # Correct request (both types of data request)
    object_ids = [_ for _ in range(1, 6)]
    object_data_ids = [_ for _ in range(6, 11)]
    resp = await cli.post("/objects/view", json={"object_ids": object_ids, "object_data_ids": object_data_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    for attr in ("objects", "object_data"):
        assert attr in data
    
    check_ids(object_ids, [data["objects"][x]["object_id"] for x in range(len(data["objects"]))], 
        "Objects view, correct request for both object attributes and data as admin, object_ids")
    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request for both object attributes and data as admin, object_data_ids")


async def test_view_objects_with_non_published_tags(cli, db_cursor):
    inserts = insert_data_for_view_tests_objects_with_non_published_tags(db_cursor)
    object_ids = inserts["inserted_object_ids"]

    # Correct request (object_ids only)
    resp = await cli.post("/objects/view", json={"object_ids": object_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()

    check_ids(object_ids, [data["objects"][x]["object_id"] for x in range(len(data["objects"]))], 
        "Objects view, correct request as admin, object_ids only")
    
    # NOTE: object_data_ids only case is checked type-specific tests

    # Correct request (both types of data request)
    object_ids = [1, 3, 5, 7, 9]
    object_data_ids = [2, 4, 6, 8, 10]
    resp = await cli.post("/objects/view", json={"object_ids": object_ids, "object_data_ids": object_data_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    
    check_ids(object_ids, [data["objects"][x]["object_id"] for x in range(len(data["objects"]))], 
        "Objects view, correct request for both object attributes and data as admin, object_ids")
    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request for both object attributes and data as admin, object_data_ids")


if __name__ == "__main__":
    run_pytest_tests(__file__)
