"""
Tests for top-level attributes of request body for /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.sessions import headers_admin_token
from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object


async def test_incorrect_values(cli, db_cursor):
    # Invalid JSON
    resp = await cli.post("/objects/bulk_upsert", json="invalid json", headers=headers_admin_token)
    assert resp.status == 400

    # Missing attributes
    for attr in ("objects", "deleted_object_ids"):
        body = get_bulk_upsert_request_body()
        body.pop(attr)
        resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect values
    incorrect_values = {
        "objects": [
            None, False, 1, "str", {}, [], [1], ["str"], 
            [get_bulk_upsert_object(i) for i in range(-100, 1)]
        ]
        # "deleted_object_ids":    # tested in test_fully_subobject_ids.py
    }
    for attr, values in incorrect_values.items():
        for value in values:
            body = get_bulk_upsert_request_body()
            body[attr] = value
            resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
            assert resp.status == 400
    
    # Unallowed attributes
    body = get_bulk_upsert_request_body()
    body["unallowed"] = "unallowed"
    resp = await cli.post("/objects/bulk_upsert", json=body, headers=headers_admin_token)
    assert resp.status == 400


if __name__ == "__main__":
    run_pytest_tests(__file__)
