"""
db/cleanup.py tests
"""
import os, sys

sys.path.insert(0, os.path.join(sys.path[0], '..'))
from backend_main.db.cleanup import close_connection_pools


async def test_cleanup(app):
    await close_connection_pools(app)
    assert app["engine"].closed
    # assert app["threaded_pool"].closed 


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
