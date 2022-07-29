import os, sys
import json
from datetime import datetime, timedelta
from uuid import uuid4
from copy import deepcopy

import psycopg2
import pytest
from pytest_aiohttp.plugin import aiohttp_client

import alembic.config

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend_main.main import create_app
from backend_main.db.init_db import migrate_as_superuser as migrate_as_superuser_, migrate as migrate_
from backend_main.config import hide_config_values

from tests.util import get_test_name
from tests.fixtures.sessions import admin_token


@pytest.fixture
def base_config():
    """ Dictionary for config parsing testing. """
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend_main/config.json.sample"))
    with open(path, "r") as stream:
        return json.load(stream)


@pytest.fixture(scope="module")
def config_path():
    """ Path to the test config file. """
    return os.path.join(
        os.path.dirname(__file__), "test_config.json"
    )

@pytest.fixture(scope="module")
def test_uuid():
    """Unique key for mock database's and database user's names in each test module."""
    return uuid4().hex


@pytest.fixture(scope="module")
def config(config_path, test_uuid):
    """ Test configuration of the app. """
    with open(config_path, "r") as stream:
        config = json.load(stream)

        # Set unique user and database names
        config["db"]["db_database"] = get_test_name(config["db"]["db_database"], test_uuid)
        config["db"]["db_username"] = get_test_name(config["db"]["db_username"], test_uuid)

        hide_config_values(config)

        return config


@pytest.fixture(scope="module")
def config_with_search(config):
    config_with_search = deepcopy(config)
    config_with_search["auxillary"]["enable_searchables_updates"] = True
    return config_with_search


@pytest.fixture(scope="module")
def init_db_cursor(config):
    """ psycopg2.Cursor object for creating and dropping test user and database. """
    connection = psycopg2.connect(host=config["db"]["db_host"], port=config["db"]["db_port"], 
                    database=config["db"]["db_init_database"].value, user=config["db"]["db_init_username"].value, 
                    password=config["db"]["db_init_password"].value)
    connection.set_session(autocommit=True)
    cursor = connection.cursor()
    yield cursor

    cursor.close()
    connection.close()


@pytest.fixture(scope="module")
def db_and_user(config, init_db_cursor):
    """ Temporary user and database for running tests. """
    init_db_cursor.execute(f"""DROP DATABASE IF EXISTS {config["db"]["db_database"].value}""")
    init_db_cursor.execute(f"""DROP USER IF EXISTS {config["db"]["db_username"].value}""")
    init_db_cursor.execute(f"""CREATE USER {config["db"]["db_username"].value} PASSWORD \'{config["db"]["db_password"].value}\' LOGIN;""")
    init_db_cursor.execute(f"""CREATE DATABASE {config["db"]["db_database"].value} ENCODING 'UTF-8' OWNER {config["db"]["db_username"].value} TEMPLATE template0;""")
    yield

    init_db_cursor.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{config["db"]["db_database"].value}'
                    AND pid <> pg_backend_pid();
    """)
    init_db_cursor.execute(f"""DROP DATABASE IF EXISTS {config["db"]["db_database"].value}""")
    init_db_cursor.execute(f"""DROP USER IF EXISTS {config["db"]["db_username"].value}""")


@pytest.fixture(scope="module")
def migrate_as_superuser(config, db_and_user):
    """ Migration commands which require superuser privilege. """
    migrate_as_superuser_(config)


@pytest.fixture(scope="module")
def migrate(config, config_path, test_uuid, db_and_user, migrate_as_superuser):
    """ Run migrations against the test database. `migrate_as_superuser` is called first. """
    migrate_(config, config_file=config_path, test_uuid=test_uuid)


@pytest.fixture(scope="module")
def db_cursor(config, migrate):
    """ psycopg2.cursor object for performing queries against the test database. """
    connection = psycopg2.connect(host=config["db"]["db_host"], port=config["db"]["db_port"], 
                    database=config["db"]["db_database"].value, user=config["db"]["db_username"].value, 
                    password=config["db"]["db_password"].value)
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
    db_cursor.execute("INSERT INTO settings VALUES ('non_admin_registration_allowed', 'FALSE', true)")

    # Insert admin
    current_time = datetime.utcnow()
    login = config["app"]["default_user"]["login"].value
    password = config["app"]["default_user"]["password"].value
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
async def app(config, db_cursor, insert_data):
    """
    aiohttp web.Application object with its own configured test database.
    """
    app = await create_app(config=config)
    yield app

    for table in app["tables"]:
        db_cursor.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")


@pytest.fixture
async def cli(aiohttp_client, app):
    """ Test client object. """
    return await aiohttp_client(app)


@pytest.fixture
async def app_with_search(config_with_search, db_cursor, insert_data):
    """
    aiohttp web.Application object with its own configured test database.
    """
    app = await create_app(config=config_with_search)
    yield app

    for table in app["tables"]:
        db_cursor.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")


@pytest.fixture
async def cli_with_search(aiohttp_client, app_with_search):
    """ Test client object. """
    return await aiohttp_client(app_with_search)
