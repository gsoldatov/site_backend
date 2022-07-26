if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests    

from tests.fixtures.tags import get_test_tag, insert_tags


async def test_correct_update(cli, db_cursor):
    # Insert mock values
    tag_list = [get_test_tag(1)]
    insert_tags(tag_list, db_cursor)

    tag = get_test_tag(3, pop_keys=["created_at", "modified_at"])
    tag["tag_id"] = 1
    resp = await cli.put("/tags/update", json={"tag": tag})
    assert resp.status == 401
    db_cursor.execute(f"SELECT tag_name FROM tags WHERE tag_id = 1")
    assert db_cursor.fetchone() == (tag_list[0]["tag_name"],)


if __name__ == "__main__":
    run_pytest_tests(__file__)
