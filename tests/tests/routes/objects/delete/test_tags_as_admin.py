"""
Tests for object tagging in /objects/delete route as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs
from tests.data_generators.sessions import headers_admin_token

from tests.data_sets.tags import tag_list

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags

from tests.request_generators.objects import get_objects_delete_body


async def test_objects_delete_route(cli, db_cursor):
    # Insert mock values
    insert_tags(tag_list, db_cursor, generate_ids=True)
    objects = [get_object_attrs(i) for i in range(1, 4)]
    insert_objects(objects, db_cursor)
    objects_tags = {1: [1, 2, 3], 2: [3, 4, 5], 3: [1, 2, 3, 4, 5]}
    insert_objects_tags([1], objects_tags[1], db_cursor)
    insert_objects_tags([2], objects_tags[2], db_cursor)
    insert_objects_tags([3], objects_tags[3], db_cursor)

    # Delete 2 objects
    body = get_objects_delete_body(object_ids=[1, 2])
    resp = await cli.delete("/objects/delete", json=body, headers=headers_admin_token)
    assert resp.status == 200

    for id in [1, 2]:
        db_cursor.execute(f"SELECT * FROM objects_tags WHERE object_id = {id}")
        assert not db_cursor.fetchone()
    db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = 3")
    assert sorted(objects_tags[3]) == sorted([r[0] for r in db_cursor.fetchall()])


if __name__ == "__main__":
    run_pytest_tests(__file__)
