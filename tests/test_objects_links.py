"""
Tests for link-specific operations.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))


from util import check_ids
from fixtures.objects import get_test_object, get_objects_attributes_list, get_test_object_data, \
    links_data_list, insert_objects, insert_links, insert_data_for_view_objects_as_anonymous
from tests.fixtures.sessions import headers_admin_token


async def test_add_as_admin(cli, db_cursor):
    # Incorrect link attributes
    for attr in [{"incorrect link attr": "123"}, {"incorrect link attr": "123", "link": "https://google.com"}]:
        link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
        link["object_data"] = attr
        resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect link value
    link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    link["object_data"] = {"link": "not a valid link"}
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute(f"SELECT object_name FROM objects") # Check that a new object was not created
    assert not db_cursor.fetchone()
    db_cursor.execute(f"SELECT link FROM links")
    assert not db_cursor.fetchone()

    # Add a correct link
    link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert "object" in resp_json
    resp_object = resp_json["object"]

    db_cursor.execute(f"SELECT link FROM links WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (link["object_data"]["link"],)


async def test_update_as_admin(cli, db_cursor):
    # Insert mock values
    obj_list = [get_test_object(1, owner_id=1, pop_keys=["object_data"]), get_test_object(2, owner_id=1, pop_keys=["object_data"])]
    l_list = [get_test_object_data(1), get_test_object_data(2)]
    insert_objects(obj_list, db_cursor)
    insert_links(l_list, db_cursor)

    # Incorrect attributes in object_data for links
    for object_data in [{}, {"link": "https://google.com", "incorrect_attr": 1}, {"link": "not a link"},
                        {"link": ""}, {"link": 123}]:
        obj = get_test_object(3, pop_keys=["created_at", "modified_at", "object_type"])
        obj["object_id"] = 1
        obj["object_data"] = object_data
        resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 400

    # Correct update (link)
    obj = get_test_object(3, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT link FROM links WHERE object_id = 1")
    assert db_cursor.fetchone() == (obj["object_data"]["link"],)


async def test_view_as_admin(cli, db_cursor):
    # Insert mock values
    insert_objects(get_objects_attributes_list(1, 10), db_cursor)
    insert_links(links_data_list, db_cursor)

    # Correct request (object_data_ids only, links), non-existing ids
    object_data_ids = [_ for _ in range(1001, 1011)]
    resp = await cli.post("/objects/view", json={"object_data_ids": object_data_ids}, headers=headers_admin_token)
    assert resp.status == 404
    
    # Correct request (object_data_ids only, links)
    object_data_ids = [_ for _ in range(1, 11)]
    resp = await cli.post("/objects/view", json={"object_data_ids": object_data_ids}, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "object_data" in data

    for field in ("object_id", "object_type", "object_data"):
        assert field in data["object_data"][0]
    assert "link" in data["object_data"][0]["object_data"]

    check_ids(object_data_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as admin, link object_data_ids only")


async def test_view_as_anonymous(cli, db_cursor):
    insert_data_for_view_objects_as_anonymous(cli, db_cursor, object_type="link")

    # Correct request (object_data_ids only, links, request all existing objects, receive only published)
    requested_object_ids = [i for i in range(1, 11)]
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]
    resp = await cli.post("/objects/view", json={"object_data_ids": requested_object_ids})
    assert resp.status == 200
    data = await resp.json()

    check_ids(expected_object_ids, [data["object_data"][x]["object_id"] for x in range(len(data["object_data"]))], 
        "Objects view, correct request as anonymous, link object_data_ids only")


async def test_delete_as_admin(cli, db_cursor):
    # Insert mock values
    obj_list = [get_test_object(1, owner_id=1, pop_keys=["object_data"]), 
        get_test_object(2, owner_id=1, pop_keys=["object_data"]), get_test_object(3, owner_id=1, pop_keys=["object_data"])]
    l_list = [get_test_object_data(1), get_test_object_data(2), get_test_object_data(3)]
    insert_objects(obj_list, db_cursor)
    insert_links(l_list, db_cursor)

    # Correct deletes (general data + link)
    resp = await cli.delete("/objects/delete", json={"object_ids": [1]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM links")
    assert db_cursor.fetchone() == (2,)
    assert db_cursor.fetchone() == (3,)
    assert not db_cursor.fetchone()

    resp = await cli.delete("/objects/delete", json={"object_ids": [2, 3]}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_id FROM links")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
