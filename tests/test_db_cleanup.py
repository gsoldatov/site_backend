"""
db/cleanup.py tests
"""
import os, sys

import pytest

sys.path.insert(0, os.path.join(sys.path[0], '..'))
from backend_main.db.cleanup import close_engine


async def test_cleanup(app):
    await close_engine(app)
    assert app["engine"].closed

if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
