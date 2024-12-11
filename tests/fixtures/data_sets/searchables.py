from datetime import datetime, timezone, timedelta

from tests.fixtures.data_generators.objects import get_test_object, get_test_object_data
from tests.fixtures.data_generators.searchables import get_test_searchable
from tests.fixtures.data_generators.tags import get_test_tag

from tests.fixtures.db_operations.objects import insert_objects, insert_links
from tests.fixtures.db_operations.searchables import insert_searchables
from tests.fixtures.db_operations.tags import insert_tags


def insert_mock_data_for_searchable_update(db_cursor):
    # Insert 3 objects
    obj_list=[
        get_test_object(1, object_name="new", object_description="", owner_id=1, pop_keys=["object_data"]),
        get_test_object(2, object_name="new", object_description="", owner_id=1, pop_keys=["object_data"]),
        get_test_object(3, object_name="new", object_description="", owner_id=1, pop_keys=["object_data"])
    ]
    insert_objects(obj_list, db_cursor)

    link_list = []
    for i in range(1, 4):
        link = get_test_object_data(i, object_type="link")
        link["link"] = ""
        link_list.append(link)

    insert_links(link_list, db_cursor)

    # Insert searchables for objects (1 searchable save after object save, 1 - before, 1 - missing)
    object_searchables = [
        get_test_searchable(object_id=1, text_a="old", modified_at=datetime.now(tz=timezone.utc) + timedelta(days=1)),
        get_test_searchable(object_id=2, text_a="old", modified_at=datetime.now(tz=timezone.utc) - timedelta(days=1))
    ]
    insert_searchables(object_searchables, db_cursor)

    # Insert 3 tags
    tag_list=[
        get_test_tag(1, tag_name="new 1", tag_description=""),
        get_test_tag(2, tag_name="new 2", tag_description=""),
        get_test_tag(3, tag_name="new 3", tag_description="")
    ]
    insert_tags(tag_list, db_cursor)

    # Insert searchables for tags (1 searchable save after tag save, 1 - before, 1 - missing)
    tag_searchables = [
        get_test_searchable(tag_id=1, text_a="old", modified_at=datetime.now(tz=timezone.utc) + timedelta(days=1)),
        get_test_searchable(tag_id=2, text_a="old", modified_at=datetime.now(tz=timezone.utc) - timedelta(days=1))
    ]
    insert_searchables(tag_searchables, db_cursor)

    return obj_list, link_list, tag_list, object_searchables, tag_searchables