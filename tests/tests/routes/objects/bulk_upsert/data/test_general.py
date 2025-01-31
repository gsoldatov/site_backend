"""
General tests for object data in /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_composite_data
from tests.data_generators.sessions import headers_admin_token

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_add_new_objects_of_different_types(cli, db_cursor):
    # Add an object of each type
    body = get_bulk_upsert_request_body(objects=[
        get_bulk_upsert_object(object_id=0, object_type="link"),
        get_bulk_upsert_object(object_id=-1, object_type="markdown"),
        get_bulk_upsert_object(object_id=-2, object_type="to_do_list"),
        get_bulk_upsert_object(object_id=-3, object_type="composite", object_data=get_composite_data()) # w/o subobjects
    ])
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)

    # Check response
    assert resp.status == 200
    data = await resp.json()
    expected_ids_and_types = [(1, "link"), (2, "markdown"), (3, "to_do_list"), (4, "composite")]
    received_ids_and_types = [(o["object_id"], o["object_type"]) for o in data["objects_data"]]
    assert received_ids_and_types == expected_ids_and_types


if __name__ == "__main__":
    run_pytest_tests(__file__)
