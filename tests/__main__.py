"""
Wrapper for parallelized test execution, which ensures that temporary users and databases are cleared if test fixtures failed to do this.
"""
from datetime import datetime
from psycopg2.extensions import cursor as CursorClass

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))

from backend_main.app.config import get_config
from backend_main.db.init_db import connect, disconnect
from tests.util import TEST_POSTFIX


def clear_test_users_and_databases():
    """
    Connects to the test database server and clears all existing temporary users and databases created during tests runs.
    """
    # Get test config
    config_file = os.path.join(os.path.dirname(__file__), "test_config.json")
    db_config = get_config(config_file=config_file).db

    # Connect to maintenance database
    cursor = connect(host=db_config.db_host, port=db_config.db_port, database=db_config.db_init_database.value,
                                user=db_config.db_init_username.value, password=db_config.db_init_password.value)
    
    try:
        # Loop through temp databases and delete them
        pattern = db_config.db_database.value + TEST_POSTFIX + "%"
        cursor.execute(f"SELECT datname FROM pg_catalog.pg_database WHERE datname LIKE '{pattern}'")
        databases = [r[0] for r in cursor.fetchall()]
        for database in databases:
            # Close existing connections before dropping
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{database}';
            """)

            cursor.execute(f"DROP DATABASE {database};")
        
        # Loop through temp users and delete them
        pattern = db_config.db_username.value + TEST_POSTFIX + "%"
        cursor.execute(f"SELECT usename FROM pg_user WHERE usename LIKE '{pattern}'")

        usernames = [r[0] for r in cursor.fetchall()]
        for username in usernames:
            # Close existing connections before dropping
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.usename = '{username}';
            """)

            cursor.execute(f"DROP ROLE {username};")
    finally:
        if type(cursor) == CursorClass:
            disconnect(cursor)
        

def main():
    clear_test_users_and_databases()

    try:
        # Get args for pytest
        args = " ".join(sys.argv[1:])

        # Change root dir
        cwd = os.getcwd()
        tests_dir = os.path.abspath(os.path.join(__file__, "..", "tests/"))
        os.chdir(tests_dir)

        # Run tests
        cmd = f'pytest -n auto --dist=loadfile --asyncio-mode=auto {args}'

        os.system(cmd)
        
        # Restore current working directory
        os.chdir(cwd)
    finally:
        clear_test_users_and_databases()


if __name__ == "__main__":
    main()
