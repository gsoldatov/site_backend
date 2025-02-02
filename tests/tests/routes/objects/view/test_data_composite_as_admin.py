"""
Tests for composite objects' data operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests


from tests.data_generators.objects import get_object_attrs, get_objects_attributes_list, get_test_object_data, \
    get_composite_data, get_composite_subobject_data
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.objects import composite_data_list, insert_data_for_composite_view_tests_objects_with_non_published_tags

from tests.db_operations.objects import insert_objects, insert_links, insert_composite, \
    insert_composite_properties

from tests.request_generators.objects import get_objects_view_request_body


async def test_view_non_existing_objects_data(cli):
    body = get_objects_view_request_body(object_ids=[], object_data_ids=[999, 1000])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 404


async def test_response_objects_data(cli, db_cursor):
    objects = [
        get_object_attrs(1, object_type="composite"),
        get_object_attrs(2), get_object_attrs(3), get_object_attrs(4)
    ]
    insert_objects(objects, db_cursor)

    composite_data = get_composite_data(subobjects=[
        get_composite_subobject_data(2, 0, 0),
        get_composite_subobject_data(3, 0, 1, is_expanded=False),
        get_composite_subobject_data(4, 0, 2, selected_tab=2)
    ])
    insert_composite([{"object_id": 1, "object_data": composite_data}], db_cursor)

    # Check if object data is correctly returned
    body = get_objects_view_request_body(object_ids=[], object_data_ids=[1])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    objects_data = data["objects_data"]
    assert len(objects_data) == 1
    assert objects_data[0]["object_id"] == 1
    assert objects_data[0]["object_type"] == "composite"
    
    received_object_data = objects_data[0]["object_data"]
    assert received_object_data["display_mode"] == composite_data["display_mode"]
    assert received_object_data["numerate_chapters"] == composite_data["numerate_chapters"]

    assert sorted(received_object_data["subobjects"], key=lambda so: so["row"]) == \
        sorted(composite_data["subobjects"], key=lambda so: so["row"])


async def test_view_non_published_composite_objects(cli, db_cursor):
    # Insert mock values
    insert_objects(get_objects_attributes_list(1, 40), db_cursor)
    insert_composite(composite_data_list, db_cursor)

    # Check if data is returned for all objects
    object_data_ids = [_ for _ in range(31, 41)]
    body = get_objects_view_request_body(object_ids=[], object_data_ids=object_data_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "objects_data" in data

    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]    
    assert sorted(object_data_ids) == sorted(received_objects_data_ids)


async def test_view_composite_objects_without_subobjects(cli, db_cursor):
    # Insert 2 objects (link & composite) + link data + composite properties
    obj_list = [get_object_attrs(10, object_type="link"),
                get_object_attrs(11, object_type="composite")]
    insert_objects(obj_list, db_cursor)

    link_data = [get_test_object_data(10, object_type="link")]
    insert_links(link_data, db_cursor)

    composite_data = [get_test_object_data(11, object_type="composite")]
    insert_composite_properties(composite_data, db_cursor)

    # Query data of both objects
    object_data_ids = [10, 11]
    body = get_objects_view_request_body(object_ids=[], object_data_ids=object_data_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)

    assert resp.status == 200
    data = await resp.json()
    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    assert sorted(object_data_ids) == sorted(received_objects_data_ids)
    for object_data in data["objects_data"]:
        object_id = object_data["object_id"]
        assert object_id in object_data_ids
        object_data_ids.remove(object_id)

        if object_id == 10:
            assert object_data["object_type"] == "link"
        else: # 11
            assert object_data["object_type"] == "composite"
            assert "subobjects" in object_data["object_data"]
            assert object_data["object_data"]["subobjects"] == []


async def test_view_composite_with_at_least_one_non_published_tag(cli, db_cursor):
    # Insert data
    insert_data_for_composite_view_tests_objects_with_non_published_tags(db_cursor)

    # Check if data is returned for all objects
    body = get_objects_view_request_body(object_ids=[], object_data_ids=[11, 12, 13])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()

    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    assert sorted([11, 12, 13]) == sorted(received_objects_data_ids)


if __name__ == "__main__":
    run_pytest_tests(__file__)
