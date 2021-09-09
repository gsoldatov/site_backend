import os, sys
import json
from datetime import datetime, timedelta
import psycopg2

import pytest
from aiohttp.pytest_plugin import loop, aiohttp_client

import alembic.config

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend_main.main import create_app
from backend_main.db.init_db import migrate_as_superuser as migrate_as_superuser_

from tests.fixtures.users import admin_token


@pytest.fixture
def base_config():
    """ Dictionary for config parsing testing. """
    return {
        "app": {
            "host": "localhost",
            "port": 55555,
            "default_user": {
                "login": "admin",
                "password": "password",
                "username": "Admin"
            },
            "token_lifetime": 10 * 60
        },
        "cors_urls": ["http://localhost:8080"],
        "db": {
            "db_host": "localhost",
            "db_port": 5432,
            "db_init_database": "init_db",
            "db_init_username": "username",
            "db_init_password": "pwd123",
            "db_database": "db",
            "db_schema": "public",
            "db_username": "username",
            "db_password": "pwd456"
    }
}


@pytest.fixture(scope="module")
def config_path():
    """ Path to the test config file. """
    return os.path.join(
        os.path.dirname(__file__), "test_config.json"
    )

@pytest.fixture(scope="module")
def config(config_path):
    """ Test configuration of the app. """
    with open(config_path, "r") as stream:
        return json.load(stream)


@pytest.fixture(scope="module")
def init_db_cursor(config):
    """ psycopg2.Cursor object for creating and dropping test user and database. """
    db_config = config["db"]
    connection = psycopg2.connect(host=db_config["db_host"], port=db_config["db_port"], 
                    database=db_config["db_init_database"], user=db_config["db_init_username"], 
                    password=db_config["db_init_password"])
    connection.set_session(autocommit=True)
    cursor = connection.cursor()
    yield cursor

    cursor.close()
    connection.close()


@pytest.fixture(scope="module")
def db_and_user(config, init_db_cursor):
    """ Temporary user and database for running tests. """
    db_config = config["db"]
    init_db_cursor.execute(f"""DROP DATABASE IF EXISTS {config["db"]["db_database"]}""")
    init_db_cursor.execute(f"""DROP USER IF EXISTS {config["db"]["db_username"]}""")
    init_db_cursor.execute(f"""CREATE USER {config["db"]["db_username"]} PASSWORD \'{config["db"]["db_password"]}\' LOGIN;""")
    init_db_cursor.execute(f"""CREATE DATABASE {config["db"]["db_database"]} ENCODING 'UTF-8' OWNER {config["db"]["db_username"]} TEMPLATE template0;""")
    yield

    init_db_cursor.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{config["db"]["db_database"]}'
                    AND pid <> pg_backend_pid();
    """)
    init_db_cursor.execute(f"""DROP DATABASE IF EXISTS {config["db"]["db_database"]}""")
    init_db_cursor.execute(f"""DROP USER IF EXISTS {config["db"]["db_username"]}""")


@pytest.fixture(scope="module")
def migrate_as_superuser(config, db_and_user):
    """ Migration commands which require superuser privilege. """
    migrate_as_superuser_(config["db"])


@pytest.fixture(scope="module")
def migrate(config_path, db_and_user, migrate_as_superuser):
    """ Run migrations against the test database. `migrate_as_superuser` is called first. """
    # Set current working directory
    cwd = os.getcwd()
    alembic_dir = os.path.join(os.path.dirname(__file__), "..", "backend_main/db")
    os.chdir(alembic_dir)

    # Run revision command
    alembic_args = ["-x", f'app_config_path="{config_path}"', "upgrade", "head"]
    alembic.config.main(argv=alembic_args)

    # Restore current working directory
    os.chdir(cwd)


@pytest.fixture(scope="module")
def db_cursor(config, migrate):
    """ psycopg2.cursor object for performing queries against the test database. """
    db_config = config["db"]
    connection = psycopg2.connect(host=db_config["db_host"], port=db_config["db_port"], 
                    database=db_config["db_database"], user=db_config["db_username"], 
                    password=db_config["db_password"])
    connection.set_session(autocommit=True)
    cursor = connection.cursor()
    yield cursor

    cursor.close()
    cursor.connection.close()


@pytest.fixture
def insert_data(config, db_cursor):
    """Insert mock data into the migrated database."""
    for table in ("settings", "users", "sessions"):
        db_cursor.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")
    
    # Insert app settings
    db_cursor.execute("INSERT INTO settings VALUES ('non_admin_registration_allowed', 'FALSE')")

    # Insert admin
    current_time = datetime.utcnow()
    login = config["app"]["default_user"]["login"]
    password = config["app"]["default_user"]["password"]
    username = config["app"]["default_user"]["username"]
    db_cursor.execute(f"""INSERT INTO users (registered_at, login, password, username, user_level, can_login, can_edit_objects)
                   VALUES ('{current_time}', '{login}', crypt('{password}', gen_salt('bf')), '{username}', 'admin', TRUE, TRUE)""")
    
    # Insert admin session
    db_cursor.execute("SELECT user_id FROM users")
    default_user_id = db_cursor.fetchone()[0]
    expiration_time = datetime.utcnow() + timedelta(minutes=15)
    db_cursor.execute(f"""INSERT INTO sessions (user_id, access_token, expiration_time)
                        VALUES ({default_user_id}, '{admin_token}', '{expiration_time}')""")

@pytest.fixture
async def app(loop, config, db_cursor, insert_data):
    """
    aiohttp web.Application object with its own configured test database.
    """
    app = await create_app(config=config)
    yield app

    schema = config["db"]["db_schema"]
    for table in app["tables"]:
        db_cursor.execute(f"TRUNCATE {schema}.{table} RESTART IDENTITY CASCADE")


@pytest.fixture
async def cli(loop, aiohttp_client, app):
    """ Test client object. """
    return await aiohttp_client(app)
