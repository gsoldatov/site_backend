"""
Tests for link-specific operations performed as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token
from tests.data_sets.objects import incorrect_link_attributes


async def test_add(cli, db_cursor):
    # Missing link object data attributes
    for attr in ["link", "show_description_as_link"]:
        link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
        link["object_data"].pop(attr)
        resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
        assert resp.status == 400

    # Incorrect and unallowed link object data attribute values
    for attr, values in incorrect_link_attributes.items():
        for value in values:
            link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
            link["object_data"][attr] = value
            resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
            assert resp.status == 400

    # Add a correct link
    link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()
    assert "object" in resp_json
    resp_object = resp_json["object"]

    db_cursor.execute(f"SELECT link FROM links WHERE object_id = {resp_object['object_id']}")
    assert db_cursor.fetchone() == (link["object_data"]["link"],)


if __name__ == "__main__":
    run_pytest_tests(__file__)
