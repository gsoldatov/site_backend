"""
Tests for scheduled database operations.
"""
from datetime import datetime, timedelta

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))

from backend_main.db_operations.scheduled.clear_expired_sessions import main as clear_expired_sessions
from backend_main.db_operations.scheduled.clear_expired_login_limits import main as clear_expired_login_limits
from backend_main.db_operations.scheduled.update_searchables import main as update_searchables

from tests.fixtures.login_rate_limits import get_test_login_rate_limit, insert_login_rate_limits
from tests.fixtures.objects import get_test_object, get_test_object_data, insert_objects, insert_links
from tests.fixtures.searchables import get_test_searchable, insert_searchables
from tests.fixtures.sessions import get_test_session, insert_sessions
from tests.fixtures.tags import get_test_tag, insert_tags
from tests.fixtures.users import get_test_user, insert_users


def test_clear_expired_sessions(db_cursor, config, app):
    # Clear sessions
    db_cursor.execute("TRUNCATE TABLE sessions")
    
    # Insert another users and sessions
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor)

    sessions = [
        get_test_session(1, access_token="-1", expiration_time=datetime.utcnow() + timedelta(seconds=-1)),
        get_test_session(2, access_token="-2", expiration_time=datetime.utcnow() + timedelta(seconds=-120)),
        get_test_session(1, access_token="1", expiration_time=datetime.utcnow() + timedelta(seconds=10)),
        get_test_session(2, access_token="2", expiration_time=datetime.utcnow() + timedelta(seconds=20))
    ]

    insert_sessions(sessions, db_cursor)

    # Run clear operation
    clear_expired_sessions(config)

    # Check if sessions were correctly removed
    db_cursor.execute("SELECT access_token FROM sessions")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == ["1", "2"]


def test_clear_expired_login_limits(db_cursor, config, app):
    # Insert data
    login_rate_limits = [
        get_test_login_rate_limit("1.1.1.1", cant_login_until=datetime.utcnow() - timedelta(hours=12, seconds=1)),
        get_test_login_rate_limit("2.2.2.2", cant_login_until=datetime.utcnow() - timedelta(days=1, hours=12, seconds=1)),
        get_test_login_rate_limit("3.3.3.3", cant_login_until=datetime.utcnow() - timedelta(hours=11, minutes=59, seconds=59)),
        get_test_login_rate_limit("4.4.4.4", cant_login_until=datetime.utcnow() + timedelta(seconds=10))
    ]

    insert_login_rate_limits(login_rate_limits, db_cursor)

    # Run clear operation
    clear_expired_login_limits(config)

    # Check if login limits were correctly removed
    db_cursor.execute("SELECT ip_address FROM login_rate_limits")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == ["3.3.3.3", "4.4.4.4"]


def test_update_searchables_without_enable_searchables_updates(db_cursor, config, app):
    # Insert mock data
    obj_list=[get_test_object(1, owner_id=1, pop_keys=["object_data"])]
    insert_objects(obj_list, db_cursor)

    searchables = [get_test_searchable(object_id=1, text_a="old", modified_at=datetime(2001, 1, 1))]
    insert_searchables(searchables, db_cursor)

    # Run script
    update_searchables("full", config)

    # Check if searchables were not updated
    db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE object_id = 1")
    assert db_cursor.fetchone() == (searchables[0]["modified_at"], searchables[0]["text_a"])


def test_update_searchables_full_mode(db_cursor, config_with_search, app_with_search):
    # Insert mock data
    _insert_mock_data_for_searchable_update(db_cursor)

    # Run script
    update_searchables("full", config_with_search)

    # Check if all objects' searchables were updated
    for object_id in range(1, 4):
        curr_time = datetime.utcnow()
        db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE object_id = %(object_id)s", {"object_id": object_id})
        modified_at, text_a = db_cursor.fetchone()
        assert curr_time - timedelta(seconds=1) < modified_at < curr_time + timedelta(seconds=1)
        assert text_a.find("new") > - 1
    
    # Check if all tags' searchables were updated
    for tag_id in range(1, 4):
        curr_time = datetime.utcnow()
        db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE tag_id = %(tag_id)s", {"tag_id": tag_id})
        modified_at, text_a = db_cursor.fetchone()
        assert curr_time - timedelta(seconds=1) < modified_at < curr_time + timedelta(seconds=1)
        assert text_a.find("new") > - 1


def test_update_searchables_missing_mode(db_cursor, config_with_search, app_with_search):
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
        curr_time = datetime.utcnow()
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
        curr_time = datetime.utcnow()
        db_cursor.execute("SELECT modified_at, text_a FROM searchables WHERE tag_id = %(tag_id)s", {"tag_id": tag_id})
        modified_at, text_a = db_cursor.fetchone()
        assert curr_time - timedelta(seconds=1) < modified_at < curr_time + timedelta(seconds=1)
        assert text_a.find("new") > - 1
    

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
        get_test_searchable(object_id=1, text_a="old", modified_at=datetime.utcnow() + timedelta(days=1)),
        get_test_searchable(object_id=2, text_a="old", modified_at=datetime.utcnow() - timedelta(days=1))
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
        get_test_searchable(tag_id=1, text_a="old", modified_at=datetime.utcnow() + timedelta(days=1)),
        get_test_searchable(tag_id=2, text_a="old", modified_at=datetime.utcnow() - timedelta(days=1))
    ]
    insert_searchables(tag_searchables, db_cursor)

    return obj_list, link_list, tag_list, object_searchables, tag_searchables



if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
