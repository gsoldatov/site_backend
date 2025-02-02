"""
Tests for link-specific operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_object_attrs, get_test_object_data
from tests.data_generators.sessions import headers_admin_token

from tests.db_operations.objects import insert_objects, insert_links


async def test_update(cli, db_cursor):
    # Insert mock values
    obj_list = [get_object_attrs(i) for i in range(1, 3)]
    l_list = [get_test_object_data(i) for i in range(1, 3)]
    insert_objects(obj_list, db_cursor)
    insert_links(l_list, db_cursor)

    # Missing link object data attributes
    for attr in ["link", "show_description_as_link"]:
        obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
        obj["object_data"].pop(attr)
        resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 400

    # Unallowed link object data attribute
    obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_data"]["unallowed"] = "some str"
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect link object data attribute values
    for attr, value in [("link", 123), ("link", False), ("show_description_as_link", 1), ("show_description_as_link", "str")]:
        obj = get_test_object(1, pop_keys=["created_at", "modified_at", "object_type"])
        obj["object_data"][attr] = value
        resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect link value (not a valid URL)
    obj = get_test_object(3, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    obj["object_data"]["link"] = "not a link"
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 400

    # Correct update (link)
    obj = get_test_object(3, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT link FROM links WHERE object_id = 1")
    assert db_cursor.fetchone() == (obj["object_data"]["link"],)


if __name__ == "__main__":
    run_pytest_tests(__file__)
