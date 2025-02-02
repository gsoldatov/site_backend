"""
Tests for to-do list object data in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs, get_test_object_data, \
    get_to_do_list_data, get_to_do_list_item_data
from tests.data_generators.sessions import headers_admin_token

from tests.db_operations.objects import insert_objects, insert_to_do_lists

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_top_level_attributes(cli, db_cursor):
    # Missing attribute
    for attr in ("sort_type", "items"):
        body = get_bulk_upsert_request_body(objects=[
            get_bulk_upsert_object(object_type="to_do_list")
        ])
        body["objects"][0]["object_data"].pop(attr)
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect values
    incorrect_values = {
        "sort_type": [None, False, 1, [], {}, "wrong str"],
        "items": [None, False, 1, "str", {}, [], ["None"], [1], ["a"], [{}]],
    }
    for attr, values in incorrect_values.items():
        for value in values:
            body = get_bulk_upsert_request_body(objects=[
                get_bulk_upsert_object(object_type="to_do_list")
            ])
            body["objects"][0]["object_data"][attr] = value
            resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
            assert resp.status == 400
    
    # Unallowed attributes
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_type="to_do_list")
    ])
    body["objects"][0]["object_data"]["unallowed"] = "unallowed"
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_incorrect_to_do_list_item_attributes(cli, db_cursor):
    # Missing attribute
    for attr in ("item_number", "item_state", "item_text", "commentary", "indent", "is_expanded"):
        body = get_bulk_upsert_request_body(objects=[
            get_bulk_upsert_object(object_type="to_do_list")
        ])
        body["objects"][0]["object_data"]["items"][0].pop(attr)
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect values
    incorrect_values = {
        "item_number": [None, False, [], {}, "str", -1],
        "item_state": [None, False, [], {}, 1, "wrong str"],
        "item_text": [None, False, [], {}, 1],
        "commentary": [None, False, [], {}, 1],
        "indent": [None, False, [], {}, "str", -1],
        "is_expanded": [None, [], {}, "str", 1]
    }
    for attr, values in incorrect_values.items():
        for value in values:
            body = get_bulk_upsert_request_body(objects=[
                get_bulk_upsert_object(object_type="to_do_list")
            ])
            body["objects"][0]["object_data"]["items"][0][attr] = value
            resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
            assert resp.status == 400
    
    # Unallowed attributes
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_type="to_do_list")
    ])
    body["objects"][0]["object_data"]["items"][0]["unallowed"] = "unallowed"
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_non_unique_item_number(cli, db_cursor):
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(
            object_type="to_do_list",
            object_data=get_to_do_list_data(items=[
                get_to_do_list_item_data(item_number=1),
                get_to_do_list_item_data(item_number=2),
                get_to_do_list_item_data(item_number=2)
            ])
        )
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_a_new_and_update_an_existing_to_do_list(cli, db_cursor):
    # Insert existing to-do list
    insert_objects([
        get_object_attrs(i, object_type="to_do_list") for i in range(1, 3)
    ], db_cursor, generate_ids=True)
    inserted_to_do_lists = [get_test_object_data(i, object_type="to_do_list") for i in range(1, 3)]
    unchanged_existing_object_data = inserted_to_do_lists[1]["object_data"]
    insert_to_do_lists(inserted_to_do_lists, db_cursor)

    # Upsert a new & an exising to-do list
    new_object_data = get_to_do_list_data(
        sort_type="default",
        items=[
            get_to_do_list_item_data(item_number=0, item_state="active"),
            get_to_do_list_item_data(item_number=1, item_state="optional"),
            get_to_do_list_item_data(item_number=2, item_state="completed"),
            get_to_do_list_item_data(item_number=3, item_state="cancelled")
        ]
    )
    updated_object_data = get_to_do_list_data(
        sort_type="state",
        items=[get_to_do_list_item_data()]
    )
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_type="to_do_list", object_data=new_object_data),
        get_bulk_upsert_object(object_id=1, object_type="to_do_list", object_data=updated_object_data)
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert sorted(data["objects_data"], key=lambda o: o["object_id"]) == [
        {"object_id": 1, "object_type": "to_do_list", "object_data": updated_object_data},
        {"object_id": 3, "object_type": "to_do_list", "object_data": new_object_data}
    ]

    # Check database (top-level attributes)
    ## New object
    db_cursor.execute("SELECT sort_type FROM to_do_lists WHERE object_id = 3")
    assert db_cursor.fetchall() == [(new_object_data["sort_type"],)]

    ## Updated object
    db_cursor.execute("SELECT sort_type FROM to_do_lists WHERE object_id = 1")
    assert db_cursor.fetchall() == [(updated_object_data["sort_type"],)]

    ## Existing object, which was not updated
    db_cursor.execute("SELECT sort_type FROM to_do_lists WHERE object_id = 2")
    assert db_cursor.fetchall() == [(unchanged_existing_object_data["sort_type"],)]

    # Check database (top-level attributes)
    ## New object
    attrs = ("item_number", "item_state", "item_text", "commentary", "indent", "is_expanded")
    db_cursor.execute(f"""
        SELECT {", ".join(attrs)}
        FROM to_do_list_items WHERE object_id = 3 ORDER BY item_number
    """)
    assert db_cursor.fetchall() == [tuple(i[a] for a in attrs) for i in new_object_data["items"]]

    ## Updated object
    db_cursor.execute(f"""
        SELECT {", ".join(attrs)}
        FROM to_do_list_items WHERE object_id = 1 ORDER BY item_number
    """)
    assert db_cursor.fetchall() == [tuple(i[a] for a in attrs) for i in updated_object_data["items"]]

    ## Existing object, which was not updated
    db_cursor.execute(f"""
        SELECT {", ".join(attrs)}
        FROM to_do_list_items WHERE object_id = 2 ORDER BY item_number
    """)
    assert db_cursor.fetchall() == [tuple(i[a] for a in attrs) for i in unchanged_existing_object_data["items"]]


async def test_to_do_list_item_numbers_are_normalized(cli, db_cursor):
    # Add a new to-do list with non-normalized to-do list items
    unnormalized_item_numbers = (3, 5, 7, 1, 2, 4)
    new_object_data = get_to_do_list_data(
        sort_type="default",
        items=[
            get_to_do_list_item_data(item_number=i, item_text=f"item {i}") for i in unnormalized_item_numbers
        ]
    )
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_type="to_do_list", object_data=new_object_data)
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    ## Status & normalized item numbers
    assert resp.status == 200
    data = await resp.json()
    sorted_items = sorted(data["objects_data"][0]["object_data"]["items"], key=lambda x: x["item_number"])
    received_item_numbers = [i["item_number"] for i in sorted_items]
    assert received_item_numbers == [0, 1, 2, 3, 4, 5]

    ## Item numbers are normalized correctly (items have expected `item_text` values)
    expected_item_texts = [f"item {i}" for i in sorted(unnormalized_item_numbers)]
    received_item_texts = [i["item_text"] for i in sorted_items]
    assert expected_item_texts == received_item_texts

    # Check database
    db_cursor.execute(f"SELECT item_number, item_text FROM to_do_list_items WHERE object_id = 1 ORDER BY item_number")
    assert db_cursor.fetchall() == [(i, f"item {n}") for i, n in enumerate(sorted(unnormalized_item_numbers))]


if __name__ == "__main__":
    run_pytest_tests(__file__)
