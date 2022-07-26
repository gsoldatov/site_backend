"""
Tests for scheduled deletion of expired login limits.
"""
from datetime import datetime, timedelta

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from backend_main.db_operations.scheduled.clear_expired_login_limits import main as clear_expired_login_limits

from tests.fixtures.login_rate_limits import get_test_login_rate_limit, insert_login_rate_limits


def test_clear_expired_login_limits(db_cursor, config):
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


if __name__ == "__main__":
    run_pytest_tests(__file__)
