if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.objects import get_test_object, insert_data_for_update_tests


async def test_correct_update(cli, db_cursor):
    # Insert mock values
    insert_data_for_update_tests(db_cursor)

    # Correct update (general attributes)
    obj = get_test_object(3, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json={"object": obj})
    assert resp.status == 401
    db_cursor.execute(f"SELECT object_name FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone() != (obj["object_name"],)


if __name__ == "__main__":
    run_pytest_tests(__file__)
