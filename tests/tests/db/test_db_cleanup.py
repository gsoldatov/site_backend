"""
db/cleanup.py tests
"""
import os, sys

sys.path.insert(0, os.path.join(sys.path[0], "../" * 3))

from backend_main.app.types import app_engine_key
from backend_main.app.db_connection import close_connection_pools
from tests.util import run_pytest_tests


async def test_cleanup_without_search(app):
    await close_connection_pools(app)
    assert app[app_engine_key].closed


# async def test_cleanup_with_search(app_with_search):
#     await close_connection_pools(app_with_search)
#     assert app_with_search[app_engine_key].closed
#     assert app_with_search["threaded_pool"].closed


if __name__ == "__main__":
    run_pytest_tests(__file__)
