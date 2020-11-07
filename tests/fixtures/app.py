"""
App and config fixtures
"""
import os, sys
import json

import pytest
from aiohttp.pytest_plugin import loop, aiohttp_client

sys.path.insert(0, os.path.join(sys.path[0], '..'))

from backend_main.main import create_app


__all__ = ["base_config", "config", "app", "cli", "init_db_cursor", "db_cursor", "migrate", "db_and_user"]


@pytest.fixture
async def cli(loop, aiohttp_client, app):
    return await aiohttp_client(app)


@pytest.fixture
async def app(loop, db_and_user, db_cursor, config):
    """
    aiohttp web.Application object with its own configured test database.
    """
    db_and_user(apply_migrations = True)
    app = await create_app(config = config)
    yield app

    cursor = db_cursor()
    schema = config["db"]["db_schema"]
    
    for table in app["tables"]:
        cursor.execute(f"TRUNCATE {schema}.{table} CASCADE")


@pytest.fixture(scope = "module")
def config():
    config_file = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) \
            + "/test_config.json"
    
    with open(config_file, "r") as stream:
        return json.load(stream)


@pytest.fixture
def base_config():
    return {
    "app": {
        "host": "localhost",
        "port": 55555
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


from fixtures.db import init_db_cursor, db_cursor, migrate, db_and_user
