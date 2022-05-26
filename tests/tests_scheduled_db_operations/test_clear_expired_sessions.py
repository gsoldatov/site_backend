"""
Tests for scheduled deletion of expired sessions.
"""
from datetime import datetime, timedelta

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from backend_main.db_operations.scheduled.clear_expired_sessions import main as clear_expired_sessions

from tests.fixtures.sessions import get_test_session, insert_sessions
from tests.fixtures.users import get_test_user, insert_users


def test_clear_expired_sessions(db_cursor, config, app):
    # Clear sessions
    db_cursor.execute("TRUNCATE TABLE sessions")
    
    # Insert another users and sessions
    insert_users([
        get_test_user(2, pop_keys=["password_repeat"]),     # another user
        get_test_user(3, can_login=False, pop_keys=["password_repeat"])     # user who can't login
    ], db_cursor)

    sessions = [
        # Sessions of active users
        get_test_session(1, access_token="-1", expiration_time=datetime.utcnow() + timedelta(seconds=-1)),
        get_test_session(2, access_token="-2", expiration_time=datetime.utcnow() + timedelta(seconds=-120)),
        get_test_session(1, access_token="1", expiration_time=datetime.utcnow() + timedelta(seconds=10)),
        get_test_session(2, access_token="2", expiration_time=datetime.utcnow() + timedelta(seconds=20)),

        # Sessions of user who can't login
        get_test_session(3, access_token="-3", expiration_time=datetime.utcnow() + timedelta(seconds=-10)),
        get_test_session(3, access_token="3", expiration_time=datetime.utcnow() + timedelta(seconds=10))
    ]

    insert_sessions(sessions, db_cursor)

    # Run clear operation
    clear_expired_sessions(config)

    # Check if sessions were correctly removed:
    # - active users still have their non-expired sessions;
    # - user, who can't login have all of his sessions deleted.
    db_cursor.execute("SELECT access_token FROM sessions")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == ["1", "2"]


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
