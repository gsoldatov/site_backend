"""
App and config fixtures
"""

import pytest
from aiohttp.pytest_plugin import loop, aiohttp_client
import json

import os, sys
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from app import create_app


__all__ = ["base_config", "config", "app", "cli", "init_db_cursor", "db_cursor", "migrate", "db_and_user"]


@pytest.fixture
async def cli(loop, aiohttp_client, app):
    return await aiohttp_client(app)


@pytest.fixture
async def app(loop, db_and_user, config):
    """
    aiohttp web.Application object with its own configured test database.
    """
    db_and_user(apply_migrations = True)
    return await create_app(config = config)


@pytest.fixture(scope = "module")
def config():
    config_file = os.path.dirname(os.path.abspath(__file__)) \
            + "/test_config.json"
    
    with open(config_file, "r") as stream:
        return json.load(stream)


@pytest.fixture
def base_config():
    return {
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


from fixtures_db import init_db_cursor, db_cursor, migrate, db_and_user
