"""
Tests for composite objects' data operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests


from tests.data_generators.objects import get_test_object, get_objects_attributes_list, get_test_object_data
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.objects import composite_data_list, insert_data_for_composite_view_tests_objects_with_non_published_tags

from tests.db_operations.objects import insert_objects, insert_links, insert_composite, \
    insert_composite_properties

from tests.request_generators.objects import get_objects_view_request_body

from tests.util import ensure_equal_collection_elements


async def test_view_non_published_composite_objects(cli, db_cursor):
    # Insert mock values
    insert_objects(get_objects_attributes_list(1, 40), db_cursor)
    insert_composite(composite_data_list, db_cursor)

    # Correct request (object_data_ids only, composite), non-existing ids
    object_data_ids = [_ for _ in range(1001, 1011)]
    body = get_objects_view_request_body(object_ids=[], object_data_ids=object_data_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 404

    # Correct request (object_data_ids only, composite)
    object_data_ids = [_ for _ in range(31, 41)]
    body = get_objects_view_request_body(object_ids=[], object_data_ids=object_data_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    assert "objects_data" in data

    for field in ("object_id", "object_type", "object_data"):
        assert field in data["objects_data"][0]
    assert "subobjects" in data["objects_data"][0]["object_data"]

    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    ensure_equal_collection_elements(object_data_ids, received_objects_data_ids,
        "Objects view, correct request, composite object_data_ids only")
    
    for attr in ["subobject_id", "row", "column", "selected_tab", "is_expanded", "show_description_composite", "show_description_as_link_composite"]:
        assert attr in data["objects_data"][0]["object_data"]["subobjects"][0]


async def test_view_composite_objects_without_subobjects(cli, db_cursor):
    # Insert 2 objects (link & composite) + link data + composite properties
    obj_list = [get_test_object(10, owner_id=1, object_type="link", pop_keys=["object_data"]),
                get_test_object(11, owner_id=1, object_type="composite", pop_keys=["object_data"])]
    insert_objects(obj_list, db_cursor)

    link_data = [get_test_object_data(10, object_type="link")]
    insert_links(link_data, db_cursor)

    composite_data = [get_test_object_data(11, object_type="composite")]
    insert_composite_properties(composite_data, db_cursor)

    # Query data of both objects
    object_data_ids = [10, 11]
    body = get_objects_view_request_body(object_ids=[], object_data_ids=object_data_ids)
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)

    print(await resp.json())
    assert resp.status == 200
    data = await resp.json()
    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    ensure_equal_collection_elements(object_data_ids, received_objects_data_ids,
        "Objects view, composite objects without subobjects")
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

    # Correct request (object_data_ids only, composite, request all composite objects, 
    # receive all objects, regardless of being tagged with non-published tags)
    body = get_objects_view_request_body(object_ids=[], object_data_ids=[11, 12, 13])
    resp = await cli.post("/objects/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()

    received_objects_data_ids = [data["objects_data"][x]["object_id"] for x in range(len(data["objects_data"]))]
    ensure_equal_collection_elements([11, 12, 13], received_objects_data_ids, 
        "Objects view, correct request as admin, composite object_data_ids only")


if __name__ == "__main__":
    run_pytest_tests(__file__)
