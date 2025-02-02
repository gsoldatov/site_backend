"""
Tests for composite object data in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs, get_test_object_data, \
    get_composite_data, get_composite_subobject_data
from tests.data_generators.sessions import headers_admin_token

from tests.db_operations.objects import insert_objects, insert_links, insert_composite

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_top_level_attributes(cli, db_cursor):
    # Missing attribute
    for attr in ("subobjects", "display_mode", "numerate_chapters"):
        body = get_bulk_upsert_request_body(objects=[
            get_bulk_upsert_object(object_type="composite")
        ])
        body["objects"][0]["object_data"].pop(attr)
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect values
    incorrect_values = {
        "subobjects": [None, False, "str", 1, {}, [1], [""]],
        "display_mode": [None, False, 1, {}, [], "wrong str"],
        "numerate_chapters": [None, 1, {}, [], "str"]
    }
    for attr, values in incorrect_values.items():
        for value in values:
            body = get_bulk_upsert_request_body(objects=[
                get_bulk_upsert_object(object_type="composite")
            ])
            body["objects"][0]["object_data"][attr] = value
            resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
            assert resp.status == 400
    
    # Unallowed attributes
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_type="composite")
    ])
    body["objects"][0]["object_data"]["unallowed"] = "unallowed"
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_incorrect_composite_item_attributes(cli, db_cursor):
    # Missing attribute
    for attr in ("subobject_id", "row", "column", "selected_tab", "is_expanded", 
                 "show_description_composite", "show_description_as_link_composite"):
        body = get_bulk_upsert_request_body(objects=[
            get_bulk_upsert_object(object_type="composite")
        ])
        body["objects"][0]["object_data"]["subobjects"][0].pop(attr)
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect values
    incorrect_values = {
        "subobject_id": [None, False, "str", [], {}],
        "row": [None, False, "str", [], {}, -1],
        "column": [None, False, "str", [], {}, -1],
        "selected_tab": [None, False, "str", [], {}, -1],
        "is_expanded": [None, "str", [], {}, 1],
        "show_description_composite": [None, False, [], {}, 1, "wrong str"],
        "show_description_as_link_composite": [None, False, [], {}, 1, "wrong str"]
    }
    for attr, values in incorrect_values.items():
        for value in values:
            body = get_bulk_upsert_request_body(objects=[
                get_bulk_upsert_object(object_type="composite")
            ])
            body["objects"][0]["object_data"]["subobjects"][0][attr] = value
            resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
            assert resp.status == 400
    
    # Unallowed attributes
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_type="composite")
    ])
    body["objects"][0]["object_data"]["subobjects"][0]["unallowed"] = "unallowed"
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_non_unique_subobject_ids(cli, db_cursor):
    # Insert objects
    insert_objects([get_object_attrs(i) for i in range(1, 4)], db_cursor)
    insert_links([get_test_object_data(i) for i in range(1, 4)], db_cursor)
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(
            object_type="composite",
            object_data=get_composite_data(subobjects=[
                get_composite_subobject_data(subobject_id=1, column=0, row=0),
                get_composite_subobject_data(subobject_id=2, column=0, row=1),
                get_composite_subobject_data(subobject_id=2, column=0, row=2)
            ])
        )
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_non_unique_subobject_positions(cli, db_cursor):
    # Insert objects
    insert_objects([get_object_attrs(i) for i in range(1, 4)], db_cursor)
    insert_links([get_test_object_data(i) for i in range(1, 4)], db_cursor)
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(
            object_type="composite",
            object_data=get_composite_data(subobjects=[
                get_composite_subobject_data(subobject_id=1, column=0, row=0),
                get_composite_subobject_data(subobject_id=2, column=1, row=0),
                get_composite_subobject_data(subobject_id=3, column=1, row=0)
            ])
        )
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_new_subobjects_without_matching_object(cli, db_cursor):
    # Add a new composite with a new subobject, which isn't passed as a separate object
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0,
            object_type="composite", object_data=get_composite_data(subobjects=[
                get_composite_subobject_data(subobject_id=1, column=0, row=0),
                get_composite_subobject_data(subobject_id=-1, column=0, row=1)
        ]))
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_upsert_objects_without_subobjects(cli, db_cursor):
    # Insert an existing object & its subobject
    insert_objects([
        get_object_attrs(1),
        get_object_attrs(2, object_type="composite"),
    ], db_cursor, generate_ids=True)
    insert_links([get_test_object_data(1)], db_cursor)
    insert_composite([get_test_object_data(2, object_type="composite")], db_cursor)

    # Upsert a new & an existing object without subobjects
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0,
            object_type="composite", object_data=get_composite_data(subobjects=[])),
        get_bulk_upsert_object(object_id=2,
            object_type="composite", object_data=get_composite_data(subobjects=[]))
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    received_subobjects = [o["object_data"]["subobjects"] for o in data["objects_data"]]
    assert received_subobjects == [[], []]

    # Check database
    db_cursor.execute("SELECT object_id FROM composite_properties WHERE object_id IN (2, 3)")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [2, 3]

    db_cursor.execute("SELECT object_id FROM composite WHERE object_id IN (2, 3)")
    assert not db_cursor.fetchone()


async def test_upsert_objects_and_modify_subobjects(cli, db_cursor):
    # Insert existing objects
    ## 101-102 = existing composite
    insert_objects([
        get_object_attrs(i, object_type="composite")
    for i in range(101, 103)], db_cursor)
    ## 11x - subobjects or 101, 12x - of 102
    suobjbect_ids = (110, 111, 112, 120, 121)
    insert_objects([
        get_object_attrs(i)
    for i in suobjbect_ids], db_cursor)
    ## object data
    insert_links([get_test_object_data(i) for i in suobjbect_ids], db_cursor)
    insert_composite([
        {"object_id": 101, "object_data": get_composite_data(subobjects=[
            get_composite_subobject_data(subobject_id=110, column=0, row=0),
            get_composite_subobject_data(subobject_id=111, column=0, row=1)
        ])},
        {"object_id": 102, "object_data": get_composite_data(subobjects=[
            get_composite_subobject_data(subobject_id=120, column=0, row=0),
            get_composite_subobject_data(subobject_id=121, column=0, row=1)
        ])}
    ], db_cursor)

    # Upsert new & existing objects
    body = get_bulk_upsert_request_body(objects=[
        ## New object with a new & an existing subobject
        get_bulk_upsert_object(object_id=0, object_name="object 0", object_type="composite", object_data=get_composite_data(
            subobjects=[
                get_composite_subobject_data(subobject_id=110, column=0, row=0), # existing subobject
                get_composite_subobject_data(subobject_id=-11, column=0, row=1)  # new subobject
            ]
        )),
        ## Existing object
        get_bulk_upsert_object(object_id=101, object_type="composite", object_data=get_composite_data(
            subobjects=[
                get_composite_subobject_data(subobject_id=110, column=0, row=0), # 110 was added before
                                                                                 # 111 is removed during upsert
                get_composite_subobject_data(subobject_id=112, column=0, row=1), # 112 is added during upsert
                get_composite_subobject_data(subobject_id=-12, column=0, row=2)  # -12 is added new
            ]
        )),

        ## Subobjects
        get_bulk_upsert_object(object_id=-11, object_name="object -11"), 
        get_bulk_upsert_object(object_id=-12, object_name="object -12"),
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check database
    ## Get new object IDs
    db_cursor.execute("SELECT object_id, object_name FROM objects WHERE object_name IN ('object 0', 'object -11', 'object -12')")
    object_name_id_map = {r[1]: r[0] for r in db_cursor.fetchall()}
    assert len(object_name_id_map) == 3
    new_composite_id = object_name_id_map["object 0"]
    new_link_1_id = object_name_id_map["object -11"]
    new_link_2_id = object_name_id_map["object -12"]

    ## Subobjects of new composite object
    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = {new_composite_id}")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [new_link_1_id, 110]

    ## Subobjects of updated composite object
    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = 101")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [new_link_2_id, 110, 112]

    ## Subobjects of unmodified existing composite object
    db_cursor.execute(f"SELECT subobject_id FROM composite WHERE object_id = 102")
    assert sorted(r[0] for r in db_cursor.fetchall()) == [120, 121]

    # Check response
    assert resp.status == 200
    data = await resp.json()
    ## Returned object IDs
    received_id_data_map = {o["object_id"]: o["object_data"] for o in data["objects_data"]}
    assert sorted(received_id_data_map.keys()) == sorted([new_composite_id, new_link_1_id, new_link_2_id, 101])

    ## Subobjects
    assert sorted(o["subobject_id"] for o in received_id_data_map[new_composite_id]["subobjects"]) == [new_link_1_id, 110]
    assert sorted(o["subobject_id"] for o in received_id_data_map[101]["subobjects"]) == [new_link_2_id, 110, 112]


async def test_new_subobjects_positions_are_normalized(cli, db_cursor):
    # Insert existing subobjects
    insert_objects([
        get_object_attrs(i)
    for i in range(10, 19)], db_cursor)
    insert_links([get_test_object_data(i) for i in range(10, 19)], db_cursor)

    # Add a new composite with its subobjects not being normalized
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_type="composite", object_data=get_composite_data(
            subobjects=[
                # first column
                get_composite_subobject_data(subobject_id=10, column=0, row=3),
                get_composite_subobject_data(subobject_id=11, column=0, row=2),
                get_composite_subobject_data(subobject_id=12, column=0, row=1),

                # second column
                get_composite_subobject_data(subobject_id=13, column=1, row=5),
                get_composite_subobject_data(subobject_id=14, column=1, row=7),
                get_composite_subobject_data(subobject_id=15, column=1, row=9),

                # third column
                get_composite_subobject_data(subobject_id=16, column=4, row=0),
                get_composite_subobject_data(subobject_id=17, column=4, row=1),
                get_composite_subobject_data(subobject_id=18, column=4, row=2),
            ]
        ))
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    expected_positions_map = {
        10: (0, 2), 11: (0, 1), 12: (0, 0),
        13: (1, 0), 14: (1, 1), 15: (1, 2),
        16: (2, 0), 17: (2, 1), 18: (2, 2)
    }
    received_positions_map = {
        so["subobject_id"]: (so["column"], so["row"])
        for so in data["objects_data"][0]["object_data"]["subobjects"]
    }
    assert received_positions_map == expected_positions_map

    # Check database
    db_cursor.execute('SELECT subobject_id, "column", "row" FROM composite WHERE object_id = 1')
    assert {r[0]: (r[1], r[2]) for r in db_cursor.fetchall()} == expected_positions_map


async def test_upsert_objects_and_check_top_level_attributes(cli, db_cursor):
    # Add new composite objects with different top-level attribute values
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_name="first", object_type="composite", object_data=get_composite_data(
            display_mode="basic", numerate_chapters=True
        )),
        get_bulk_upsert_object(object_id=-1, object_name="second", object_type="composite", object_data=get_composite_data(
            display_mode="grouped_links", numerate_chapters=True
        )),
        get_bulk_upsert_object(object_id=-2, object_name="third", object_type="composite", object_data=get_composite_data(
            display_mode="multicolumn", numerate_chapters=False
        )),
        get_bulk_upsert_object(object_id=-3, object_name="fourth", object_type="composite", object_data=get_composite_data(
            display_mode="chapters", numerate_chapters=False
        )),
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check database
    db_cursor.execute("SELECT object_id, object_name FROM objects")
    ## Get ID map for new objects
    name_id_map = {r[1] : r[0] for r in db_cursor.fetchall()}

    ## Check if composite properties are added correctly
    expected_attrs_map = {
        name_id_map[o["object_name"]]: (o["object_data"]["display_mode"], o["object_data"]["numerate_chapters"])
    for o in body["objects"]}
    db_cursor.execute("SELECT object_id, display_mode, numerate_chapters FROM composite_properties")
    assert {r[0]: (r[1], r[2]) for r in db_cursor.fetchall()} == expected_attrs_map

    # Check response
    assert resp.status == 200
    data = await resp.json()
    received_attributes_map = {
        o["object_id"]: (o["object_data"]["display_mode"], o["object_data"]["numerate_chapters"])
    for o in data["objects_data"]}
    assert received_attributes_map == expected_attrs_map


async def test_upsert_objects_and_check_subobject_attributes(cli, db_cursor):
    # Insert existing subobjects
    insert_objects([
        get_object_attrs(i)
    for i in range(10, 13)], db_cursor)
    insert_links([get_test_object_data(i) for i in range(10, 13)], db_cursor)

    # Add a new composite object with different subobject properties' values
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_type="composite", object_data=get_composite_data(
            subobjects=[
                get_composite_subobject_data(
                    subobject_id=10, column=0, row=0,
                    selected_tab=0,
                    is_expanded=True,
                    show_description_composite="yes",
                    show_description_as_link_composite="no"
                ),
                get_composite_subobject_data(
                    subobject_id=11, column=0, row=1,
                    selected_tab=1,
                    is_expanded=False,
                    show_description_composite="no",
                    show_description_as_link_composite="inherit"
                ),
                get_composite_subobject_data(
                    subobject_id=12, column=1, row=0,
                    selected_tab=2,
                    is_expanded=True,
                    show_description_composite="inherit",
                    show_description_as_link_composite="yes"
                )
            ]
        ))
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    
    attrs = ("subobject_id", "column", "row", "selected_tab", "is_expanded", "show_description_composite",
             "show_description_as_link_composite")
    expected_data = body["objects"][0]["object_data"]["subobjects"]
    received_data = data["objects_data"][0]["object_data"]["subobjects"]
    assert received_data == expected_data

    # Check database
    expected_db_data = sorted(
        (tuple(so[attr] for attr in attrs) for so in expected_data)
        , key=lambda x: x[0]
    )
    db_cursor.execute(f"""SELECT {", ".join(f'"{a}"' for a in attrs)} FROM composite ORDER BY subobject_id""") ## Enquote column names in query
    assert db_cursor.fetchall() == expected_db_data


if __name__ == "__main__":
    run_pytest_tests(__file__)
