"""
Tests for anonymous access of /objects/upsert route.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 7)))
    from tests.util import run_pytest_tests

from tests.request_generators.objects import get_bulk_upsert_request_body


async def test_try_upserting_as_anonymous(cli, db_cursor):
    body = get_bulk_upsert_request_body()
    resp = await cli.post("/objects/bulk_upsert", json=body)
    assert resp.status == 401


if __name__ == "__main__":
    run_pytest_tests(__file__)
