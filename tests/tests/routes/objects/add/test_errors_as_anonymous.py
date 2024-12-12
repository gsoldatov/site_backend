if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object


async def test_add_a_correct_object_as_anonymous(cli, db_cursor):
    link = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli.post("/objects/add", json={"object": link})
    assert resp.status == 401

    db_cursor.execute(f"SELECT object_name FROM objects")
    assert not db_cursor.fetchone()


if __name__ == "__main__":
    run_pytest_tests(__file__)
