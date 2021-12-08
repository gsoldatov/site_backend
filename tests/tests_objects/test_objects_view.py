if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.util import check_ids
from tests.fixtures.objects import get_objects_attributes_list,\
    links_data_list, insert_objects, insert_links, insert_data_for_view_objects_as_anonymous
from tests.fixtures.sessions import headers_admin_token


async def test_incorrect_request_body_as_admin(cli):
    # Incorrect request body
    resp = await cli.post("/objects/view", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    for payload in [{}, {"object_ids": []}, {"object_ids": [1, -1]}, {"object_ids": [1, "abc"]},
                        {"object_data_ids": []}, {"object_data_ids": [1, -1]}, {"object_data_ids": [1, "abc"]},
                        {"object_ids": [1], "object_data_ids": [-1]}, {"object_ids": [-1], "object_data_ids": [1]}]:
        resp = await cli.post("/objects/view", json=payload, headers=headers_admin_token)
        assert resp.status == 400


async def test_view_non_existing_objects_as_admin(cli):
    for key in {"object_ids", "object_data_ids"}:
        resp = await cli.post("/objects/view", json={key: [999, 1000]}, headers=headers_admin_token)
        assert resp.status == 404


async def test_view_existing_objects_as_admin(cli, db_cursor):
    # Insert mock values
    insert_objects(get_objects_attributes_list(1, 10), db_cursor)
    insert_links(links_data_list, db_cursor)
    
    # Correct request (object_ids only)
    object_ids = [_ for _ in range(1, 11)]
    resp = await cli.post("/objects/view", json={"object_ids": object_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "objects" in data

    for field in ("object_id", "object_type", "object_name", "object_description", "created_at", "modified_at", "is_published", "display_in_feed", "feed_timestamp", "show_description"):
        assert field in data["objects"][0]

    check_ids(object_ids, [data["objects"][x]["object_id"] for x in range(len(data["objects"]))], 
        "Objects view, correct request as admin, object_ids only")
    
    # Correct request (object_data_ids only) is checked type-specific tests

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


async def test_view_existing_objects_as_anonymous(cli, db_cursor):
    insert_data_for_view_objects_as_anonymous(cli, db_cursor)
    
    # Correct request (object_ids only, published objects only are returned)
    requested_object_ids = [i for i in range(1, 11)]
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]
    resp = await cli.post("/objects/view", json={"object_ids": requested_object_ids})
    assert resp.status == 200
    data = await resp.json()
    check_ids(expected_object_ids, [data["objects"][x]["object_id"] for x in range(len(data["objects"]))], 
        "Objects view, correct request as anonymous, object_ids only")
    
    # Correct request (object_data_ids only) is checked type-specific tests

    # Correct request (both types of data request, published objects only are returned)
    requested_object_ids = [i for i in range(1, 11)]
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]
    requested_object_data_ids = [i for i in range(3, 9)]
    expected_object_data_ids = [i for i in range(3, 9) if i % 2 == 0]
    resp = await cli.post("/objects/view", json={"object_ids": requested_object_ids, "object_data_ids": requested_object_data_ids})
    assert resp.status == 200
    data = await resp.json()
    
    check_ids(expected_object_ids, [data["objects"][x]["object_id"] for x in range(len(data["objects"]))], 
        "Objects view, correct request for both object attributes and data as anonymous, object_ids")
    check_ids(expected_object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request for both object attributes and data as anonymous, object_data_ids")


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
