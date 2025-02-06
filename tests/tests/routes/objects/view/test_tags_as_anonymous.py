"""
Tests for viewing objects' tags in /objects/view route as anonymous.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_object_attrs
from tests.data_generators.tags import get_test_tag

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags

from tests.request_generators.objects import get_objects_view_request_body


async def test_objects_view_route(cli, db_cursor):
    # Insert mock data:
    # - tags: 1, 2, 3 - published, 4 - not published
    # - objects tags: 1: [], 2: [1, 2], 3: [1, 2, 3], 4: [1, 2, 3, 4]
    insert_objects([
        get_object_attrs(object_id=i, is_published=True) for i in range(1, 5)
    ], db_cursor)
    insert_tags([
        get_test_tag(i, is_published=i != 4) for i in range(1, 5)
    ], db_cursor)
    insert_objects_tags([2], [1, 2], db_cursor)
    insert_objects_tags([3], [1, 2, 3], db_cursor)
    insert_objects_tags([4], [1, 2, 3, 4], db_cursor)
    
    # View objects attributes and tags
    body = get_objects_view_request_body(object_ids=[1, 2, 3, 4], object_data_ids=[])
    resp = await cli.post("/objects/view", json=body)
    assert resp.status == 200
    data = await resp.json()

    ## Check if expected object IDs returned (4 not returned, due to being tagged with a hidden tag)
    assert sorted(o["object_id"] for o in data["objects_attributes_and_tags"]) == [1, 2, 3]

    ## Check returned `current_tag_ids`
    received_current_tag_ids = [
        sorted(o["current_tag_ids"])
        for o in sorted(
            (a for a in data["objects_attributes_and_tags"])
            , key=lambda x: x["object_id"]
        )
    ]
    assert received_current_tag_ids == [[], [1, 2], [1, 2, 3]]  # for objects 1, 2 & 3


if __name__ == "__main__":
    run_pytest_tests(__file__)
