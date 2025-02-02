"""
Tests for object tagging in /objects/... and /tags/... routes performed as anonymous.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs
from tests.data_generators.tags import get_test_tag
from tests.data_generators.users import get_test_user

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags
from tests.db_operations.users import insert_users

from tests.request_generators.objects import get_update_tags_request_body


async def test_objects_update_tags_route(cli, db_cursor):
    # Insert mock data
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user

    object_attributes = [get_object_attrs(i, owner_id=1 if i <= 1 else 2) for i in range(1, 3)]
    insert_objects(object_attributes, db_cursor)

    tags = [get_test_tag(i) for i in range(1, 11)]
    insert_tags(tags, db_cursor)

    tags_objects = {1: [1, 2, 3, 4, 5], 2: [1, 2, 6, 7]}
    for k in tags_objects:
        insert_objects_tags([k], tags_objects[k], db_cursor)
        
    # Try to update objects tags with different parameters
    for body in [
        get_update_tags_request_body(object_ids=[1], added_tags=[6, 7, 8, "new tag"], removed_tag_ids=[]),
        get_update_tags_request_body(object_ids=[1], added_tags=[], removed_tag_ids=[1, 2, 3]),
        get_update_tags_request_body(object_ids=[2], added_tags=[4, 5, 8, "new tag"], removed_tag_ids=[]),
        get_update_tags_request_body(object_ids=[2], added_tags=[], removed_tag_ids=[1, 2, 7])
    ]:
        resp = await cli.put("/objects/update_tags", json=body)
        assert resp.status == 401


if __name__ == "__main__":
    run_pytest_tests(__file__)
