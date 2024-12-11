"""
Tests for scheduled recalculations of `searchables` table.
"""
from datetime import datetime, timezone, timedelta

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from backend_main.db_operations.scheduled.update_searchables import main as update_searchables

from tests.fixtures.objects import get_test_object, get_test_object_data, insert_objects, insert_links
from tests.fixtures.data_generators.searchables import get_test_searchable
from tests.fixtures.db_operations.searchables import insert_searchables
from tests.fixtures.tags import get_test_tag, insert_tags


def test_disabled_searchables_updates(db_cursor, config, app):
    # Insert mock data
    obj_list=[get_test_object(1, owner_id=1, pop_keys=["object_data"])]
    insert_objects(obj_list, db_cursor)

    searchables = [get_test_searchable(object_id=1, text_a="old", modified_at=datetime(2001, 1, 1, tzinfo=timezone.utc))]
    insert_searchables(searchables, db_cursor)

    # Run script
    update_searchables("full", config)

    # Check if searchables were not updated
    db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE object_id = 1")
    assert db_cursor.fetchone() == (searchables[0]["modified_at"], searchables[0]["text_a"])


def test_full_mode(db_cursor, config_with_search, app_with_search):
    # Insert mock data
    _insert_mock_data_for_searchable_update(db_cursor)

    # Run script
    update_searchables("full", config_with_search)

    # Check if all objects' searchables were updated
    for object_id in range(1, 4):
        curr_time = datetime.now(tz=timezone.utc)
        db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE object_id = %(object_id)s", {"object_id": object_id})
        modified_at, text_a = db_cursor.fetchone()
        assert curr_time - timedelta(seconds=1) < modified_at < curr_time + timedelta(seconds=1)
        assert text_a.find("new") > - 1
    
    # Check if all tags' searchables were updated
    for tag_id in range(1, 4):
        curr_time = datetime.now(tz=timezone.utc)
        db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE tag_id = %(tag_id)s", {"tag_id": tag_id})
        modified_at, text_a = db_cursor.fetchone()
        assert curr_time - timedelta(seconds=1) < modified_at < curr_time + timedelta(seconds=1)
        assert text_a.find("new") > - 1


def test_missing_mode(db_cursor, config_with_search, app_with_search):
    # Insert mock data
    obj_list, link_list, tag_list, object_searchables, tag_searchables = _insert_mock_data_for_searchable_update(db_cursor)

    # Run script
    update_searchables("missing", config_with_search)

    # Check if object searchables saved after object save were not updated
    db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE object_id = 1")
    modified_at, text_a = db_cursor.fetchone()
    assert modified_at == object_searchables[0]["modified_at"]
    assert text_a == object_searchables[0]["text_a"]

    # Check if object searchables not saved after object save were updated
    for object_id in range(2, 4):
        curr_time = datetime.now(tz=timezone.utc)
        db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE object_id = %(object_id)s", {"object_id": object_id})
        modified_at, text_a = db_cursor.fetchone()
        assert curr_time - timedelta(seconds=1) < modified_at < curr_time + timedelta(seconds=1)
        assert text_a.find("new") > - 1
    
    # Check if tag searchables saved after tag save were not updated
    db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE tag_id = 1")
    modified_at, text_a = db_cursor.fetchone()
    assert modified_at == tag_searchables[0]["modified_at"]
    assert text_a == tag_searchables[0]["text_a"]

    # Check if tag searchables not saved after tag save were updated
    for tag_id in range(2, 4):
        curr_time = datetime.now(tz=timezone.utc)
        db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE tag_id = %(tag_id)s", {"tag_id": tag_id})
        modified_at, text_a = db_cursor.fetchone()
        assert curr_time - timedelta(seconds=1) < modified_at < curr_time + timedelta(seconds=1)
        assert text_a.find("new") > - 1
    

# TODO move into a separate file
def _insert_mock_data_for_searchable_update(db_cursor):
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


if __name__ == "__main__":
    run_pytest_tests(__file__)
