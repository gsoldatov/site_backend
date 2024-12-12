if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.objects import incorrect_object_values


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.post("/objects/add", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Required attributes missing
    for attr in ("object_type", "object_name", "object_description", "is_published", "display_in_feed", "feed_timestamp", "show_description"):
        link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
        link.pop(attr)
        resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
        assert resp.status == 400

    # Unallowed attributes
    link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    link["unallowed"] = "unallowed"
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect values for general attributes
    for k, v in incorrect_object_values:
        if k != "object_id":
            link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
            link[k] = v
            resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
            assert resp.status == 400


async def test_add_object_with_incorrect_data(cli):
    # Non-existing owner_id
    link = get_test_object(1, owner_id=1000, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": link}, headers=headers_admin_token)
    assert resp.status == 400


if __name__ == "__main__":
    run_pytest_tests(__file__)
