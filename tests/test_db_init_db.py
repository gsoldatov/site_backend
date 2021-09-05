"""
db/init_db.py tests
"""
import os, sys
import shutil

import pytest
import psycopg2

sys.path.insert(0, os.path.join(sys.path[0], '..'))
from backend_main.db.init_db import (connect, disconnect, create_user, create_db,
                        migrate_as_superuser, migrate)


def test_connect_disconnect(config):
    try:
        db_config = config["db"]
        cursor = connect(host=db_config["db_host"], port=db_config["db_port"], 
                    database=db_config["db_init_database"], user=db_config["db_init_username"], 
                    password=db_config["db_init_password"])
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)

        disconnect(cursor)
        assert cursor.closed
        assert cursor.connection.closed
    except Exception as e:
        pytest.fail(str(e))


def test_create_user(config, init_db_cursor):
    db_config = config["db"]
    create_user(init_db_cursor, db_config["db_username"], db_config["db_password"])
    init_db_cursor.execute(f"SELECT usename FROM pg_user where usename = \'{db_config['db_username']}\'")
    assert init_db_cursor.fetchone() == (db_config["db_username"],)


def test_create_db(config, init_db_cursor):
    db_config = config["db"]
    create_db(init_db_cursor, db_config["db_database"], db_config["db_username"], False)
    init_db_cursor.execute(f"SELECT datname FROM pg_database where datname = \'{db_config['db_database']}\'")
    assert init_db_cursor.fetchone() == (db_config["db_database"],)

    init_db_cursor.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{db_config["db_database"]}'
                    AND pid <> pg_backend_pid();
    """)
    init_db_cursor.execute(f"""DROP DATABASE IF EXISTS {db_config["db_database"]}""")
    init_db_cursor.execute(f"""DROP USER IF EXISTS {db_config["db_username"]}""")


def test_migrate(config_path, config, db_and_user):
    db_config = config["db"]
    migrate_as_superuser(db_config)
    migrate(config_file=config_path)

    connection = psycopg2.connect(host=db_config["db_host"], port=db_config["db_port"], 
                    database=db_config["db_database"], user=db_config["db_username"], 
                    password=db_config["db_password"])
    connection.set_session(autocommit=True)
    cursor = connection.cursor()

    cursor.execute("SELECT tablename FROM pg_tables WHERE tablename = 'alembic_version'")
    assert cursor.fetchone() == ("alembic_version",)

    cursor.close()
    connection.close()


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
