if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.tags import get_test_tag


async def test_add_a_correct_tag_as_anonymous(cli, db_cursor):
    tag = get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])
    resp = await cli.post("/tags/add", json={"tag": tag})
    assert resp.status == 401

    db_cursor.execute(f"SELECT tag_name FROM tags")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
