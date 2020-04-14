"""
db/cleanup.py tests
"""
import pytest
from fixtures_app import app, init_db_cursor, db_and_user, migrate, config

import os, sys
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from db.cleanup import close_engine


async def test_cleanup(app):
    await close_engine(app)
    assert app["engine"].closed

if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
