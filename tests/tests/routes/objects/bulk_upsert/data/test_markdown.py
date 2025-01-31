"""
Tests for markdown object data in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_test_object_data, get_markdown_data
from tests.data_generators.sessions import headers_admin_token

from tests.db_operations.objects import insert_objects, insert_markdown

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_request_body(cli, db_cursor):
    # Missing attribute
    for attr in ("raw_text",):
        body = get_bulk_upsert_request_body(objects=[
            get_bulk_upsert_object(object_type="markdown")
        ])
        body["objects"][0]["object_data"].pop(attr)
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect values
    incorrect_values = {
        "raw_text": [None, False, 1, [], {}, ""],
    }
    for attr, values in incorrect_values.items():
        for value in values:
            body = get_bulk_upsert_request_body(objects=[
                get_bulk_upsert_object(object_type="markdown")
            ])
            body["objects"][0]["object_data"][attr] = value
            resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
            assert resp.status == 400
    
    # Unallowed attributes
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_type="markdown")
    ])
    body["objects"][0]["object_data"]["unallowed"] = "unallowed"
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_add_a_new_and_update_an_existing_markdown(cli, db_cursor):
    # Insert existing markdown
    insert_objects([
        get_test_object(i, object_type="markdown", owner_id=1, pop_keys=["object_data"]) for i in range(1, 3)
    ], db_cursor, generate_ids=True)
    inserted_markdown = [get_test_object_data(i, object_type="markdown") for i in range(1, 3)]
    unchanged_existing_object_data = inserted_markdown[1]["object_data"]
    insert_markdown(inserted_markdown, db_cursor)

    # Upsert a new & an exising markdown
    new_object_data = get_markdown_data(raw_text="new markdown text")
    updated_object_data = get_markdown_data(raw_text="updated markdown text")
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_type="markdown", object_data=new_object_data),
        get_bulk_upsert_object(object_id=1, object_type="markdown", object_data=updated_object_data)
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    assert sorted(data["objects_data"], key=lambda o: o["object_id"]) == [
        {"object_id": 1, "object_type": "markdown", "object_data": updated_object_data},
        {"object_id": 3, "object_type": "markdown", "object_data": new_object_data}
    ]

    # Check database
    ## New object
    db_cursor.execute("SELECT raw_text FROM markdown WHERE object_id = 3")
    assert db_cursor.fetchall() == [(new_object_data["raw_text"],)]

    ## Updated object
    db_cursor.execute("SELECT raw_text FROM markdown WHERE object_id = 1")
    assert db_cursor.fetchall() == [(updated_object_data["raw_text"],)]

    ## Existing object, which was not updated
    db_cursor.execute("SELECT raw_text FROM markdown WHERE object_id = 2")
    assert db_cursor.fetchall() == [(unchanged_existing_object_data["raw_text"],)]


if __name__ == "__main__":
    run_pytest_tests(__file__)
