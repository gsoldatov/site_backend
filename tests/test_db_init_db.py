"""
db/init_db.py tests
"""
import os, sys
import shutil

import pytest
import psycopg2

sys.path.insert(0, os.path.join(sys.path[0], '..'))

from backend_main.db.init_db import (connect, disconnect, create_user, create_db,
                        create_schema, create_flyway_conf, migrate_db)
from fixtures.db import *


def test_connect_disconnect(config):
    try:
        db_config = config["db"]
        cursor = connect(host = db_config["db_host"], port = db_config["db_port"], 
                    database = db_config["db_init_database"], user = db_config["db_init_username"], 
                    password = db_config["db_init_password"])
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
    create_db(init_db_cursor, db_config["db_database"], db_config["db_username"])
    init_db_cursor.execute(f"SELECT datname FROM pg_database where datname = \'{db_config['db_database']}\'")
    assert init_db_cursor.fetchone() == (db_config["db_database"],)


def test_create_schema(config, db_cursor):
    cursor = db_cursor(apply_migrations = False)
    db_config = config["db"]
    create_schema(db_config["db_host"], db_config["db_port"], db_config["db_database"], db_config["db_username"], db_config["db_password"], db_config["db_schema"])
    cursor.execute(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = \'{db_config['db_schema']}\'")
    assert cursor.fetchone() == (db_config["db_schema"],)


def test_create_flyway_conf(config, migration_folder):
    create_flyway_conf(config["db"], migration_folder)
    config_file = migration_folder + "/flyway.conf"
    assert os.path.exists(config_file)
    
    with open(config_file) as stream:
        config = "".join(stream.readlines())
        for setting in ("flyway.url", "flyway.user", "flyway.password",
                        "flyway.schemas", "flyway.locations"):
            assert config.index(setting) >= 0


def test_migrate(migration_folder, db_cursor):
    cursor = db_cursor(apply_migrations = False)
    migrate_db(migration_folder)
    cursor.execute("SELECT tablename FROM pg_tables WHERE tablename = 'test'")
    assert cursor.fetchone() == ("test",)


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
