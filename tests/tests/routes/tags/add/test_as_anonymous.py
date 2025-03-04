if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.request_generators.tags import get_tags_add_request_body


async def test_add_a_correct_tag_as_anonymous(cli, db_cursor):
    body = get_tags_add_request_body()
    resp = await cli.post("/tags/add", json=body)
    assert resp.status == 401

    db_cursor.execute(f"SELECT tag_name FROM tags")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
