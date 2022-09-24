if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.objects import insert_data_for_delete_tests


async def test_delete_objects_as_anonymous(cli, db_cursor):
    insert_data_for_delete_tests(db_cursor)

    # Correct deletes (general data + link)
    resp = await cli.delete("/objects/delete", json={"object_ids": [2, 3]})
    assert resp.status == 401
    db_cursor.execute(f"SELECT count(*) FROM objects")
    assert db_cursor.fetchone()[0] == 3


if __name__ == "__main__":
    run_pytest_tests(__file__)
