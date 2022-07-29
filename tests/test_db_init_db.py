"""
db/init_db.py tests
"""
import os, sys

import pytest
import psycopg2

sys.path.insert(0, os.path.join(sys.path[0], '..'))
from backend_main.db.init_db import (connect, disconnect, create_user, create_db,
                        migrate_as_superuser, migrate)
from tests.util import run_pytest_tests


def test_connect_disconnect(config):
    try:
        db_config = config["db"]
        cursor = connect(host=db_config["db_host"], port=db_config["db_port"], 
                    database=db_config["db_init_database"].value, user=db_config["db_init_username"].value, 
                    password=db_config["db_init_password"].value)
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)

        disconnect(cursor)
        assert cursor.closed
        assert cursor.connection.closed
    except Exception as e:
        pytest.fail(str(e))


def test_create_user(config, init_db_cursor):
    db_config = config["db"]
    create_user(config, init_db_cursor)
    init_db_cursor.execute(f"SELECT usename FROM pg_user where usename = \'{db_config['db_username'].value}\'")
    assert init_db_cursor.fetchone() == (db_config["db_username"].value,)


def test_create_db(config, init_db_cursor):
    db_config = config["db"]
    create_db(config, init_db_cursor)
    init_db_cursor.execute(f"SELECT datname FROM pg_database where datname = \'{db_config['db_database'].value}\'")
    assert init_db_cursor.fetchone() == (db_config["db_database"].value,)

    init_db_cursor.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{db_config["db_database"].value}'
                    AND pid <> pg_backend_pid();
    """)
    init_db_cursor.execute(f"""DROP DATABASE IF EXISTS {db_config["db_database"].value}""")
    init_db_cursor.execute(f"""DROP USER IF EXISTS {db_config["db_username"].value}""")


def test_migrate(config_path, test_uuid, config, db_and_user):
    db_config = config["db"]
    migrate_as_superuser(config)
    migrate(config, config_file=config_path, test_uuid=test_uuid)

    connection = psycopg2.connect(host=db_config["db_host"], port=db_config["db_port"], 
                    database=db_config["db_database"].value, user=db_config["db_username"].value, 
                    password=db_config["db_password"].value)
    connection.set_session(autocommit=True)
    cursor = connection.cursor()

    cursor.execute("SELECT tablename FROM pg_tables WHERE tablename = 'alembic_version'")
    assert cursor.fetchone() == ("alembic_version",)

    cursor.close()
    connection.close()


if __name__ == "__main__":
    run_pytest_tests(__file__)
