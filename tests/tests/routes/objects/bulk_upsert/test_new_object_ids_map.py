"""
Tests for new object IDs mapping in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs, get_link_data, \
    get_composite_data, get_composite_subobject_data
from tests.data_generators.sessions import headers_admin_token

from tests.db_operations.objects import insert_objects, insert_links

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_id_mapping_of_new_objects(cli, db_cursor):
    # Insert an existing object
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)
    insert_links([{"object_id": 1, "object_data": get_link_data(1)}], db_cursor)

    # Add several new objects and update an existing
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_name="first", object_type="link"),
        get_bulk_upsert_object(object_id=-1, object_name="second", object_type="markdown"),
        get_bulk_upsert_object(object_id=-2, object_name="third", object_type="to_do_list"),
        get_bulk_upsert_object(object_id=-3, object_name="fourth", object_type="composite",
                               object_data=get_composite_data(subobjects=[])),
        
        get_bulk_upsert_object(object_id=1, object_name="updated existing")
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()

    ## ID mapping is correct
    assert sorted(
        data["new_object_ids_map"].items(), key=lambda x: x[1]
    ) == [("0", 2), ("-1", 3), ("-2", 4), ("-3", 5)]    # keys are serialized to strings when dumping response into JSON

    ## Object attributes have correctly mapped IDs
    assert sorted(
        ((o["object_id"], o["object_name"]) for o in data["objects_attributes_and_tags"])
        , key=lambda x: x[0]
    ) == [(1, "updated existing"), (2, "first"), (3, "second"), (4, "third"), (5, "fourth")]

    ## Objects data has correctly mapped IDs
    assert sorted(
        ((o["object_id"], o["object_type"]) for o in data["objects_data"])
        , key=lambda x: x[0]
    ) == [(1, "link"), (2, "link"), (3, "markdown"), (4, "to_do_list"), (5, "composite")]


async def test_id_mapping_of_new_subobjects(cli, db_cursor):
    # Insert an existing object
    insert_objects([get_object_attrs(1)], db_cursor, generate_ids=True)
    insert_links([{"object_id": 1, "object_data": get_link_data(1)}], db_cursor)

    # Add a composite object with new & existing subobjects
    body = get_bulk_upsert_request_body(objects=[
        ## Composite object
        get_bulk_upsert_object(object_id=0, object_type="composite", object_data=get_composite_data(
            subobjects=[
                get_composite_subobject_data(-1, 0, 0),
                get_composite_subobject_data(-2, 0, 1),
                get_composite_subobject_data(1, 0, 2),
                get_composite_subobject_data(-3, 0, 3)
            ]
        )),

        ## New subobjects
        get_bulk_upsert_object(object_id=-1),
        get_bulk_upsert_object(object_id=-2),
        get_bulk_upsert_object(object_id=-3)
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()

    ## ID mapping is correct
    assert sorted(
        data["new_object_ids_map"].items(), key=lambda x: x[1]
    ) == [("0", 2), ("-1", 3), ("-2", 4), ("-3", 5)]    # keys are serialized to strings when dumping response into JSON

    ## Subobject IDs are correctly mapped
    composite_object_data = [o["object_data"] for o in data["objects_data"] if o["object_type"] == "composite"][0]
    assert sorted(
        ((so["subobject_id"], so["column"], so["row"]) for so in composite_object_data["subobjects"])
        , key=lambda x: x[2]
    ) == [(3, 0, 0), (4, 0, 1), (1, 0, 2), (5, 0, 3)]


if __name__ == "__main__":
    run_pytest_tests(__file__)
