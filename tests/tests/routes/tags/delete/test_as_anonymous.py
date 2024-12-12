if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.tags import get_test_tag

from tests.fixtures.db_operations.tags import insert_tags


async def test_delete_tags_as_anonymous(cli, db_cursor):
    # Insert mock values
    tag_list = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
    insert_tags(tag_list, db_cursor)

    # Correct deletes
    resp = await cli.delete("/tags/delete", json={"tag_ids": [2, 3]})
    assert resp.status == 401
    db_cursor.execute(f"SELECT count(*) FROM tags")
    assert db_cursor.fetchone()[0] == 3


if __name__ == "__main__":
    run_pytest_tests(__file__)
