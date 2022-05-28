if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(sys.path[0]))

import asyncio

from aiohttp import web
from psycopg2.errors import OperationalError

from backend_main.config import get_config
from backend_main.cors import setup_cors
from backend_main.db.setup import setup_connection_pools
from backend_main.middlewares.auth import auth_middleware
from backend_main.middlewares.errors import error_middleware
from backend_main.middlewares.connection import connection_middleware
from backend_main.middlewares.threading import threading_middleware

from backend_main.db.tables import get_tables
from backend_main.routes import setup_routes


async def create_app(config_file = None, config = None):
    try:
        app = web.Application(middlewares=[error_middleware, threading_middleware, connection_middleware, auth_middleware])
        app["config"] = config if config and type(config) == dict else get_config(config_file)
        
        await setup_connection_pools(app)
        
        app["tables"] = get_tables()[0]

        setup_routes(app)
        
        setup_cors(app)

        # TODO log app start
        return app
    except OperationalError:
        print("Failed to setup database connection pools.")    # TODO log connection pool setup error
        raise web.GracefulExit()    # Close the app gracefully
    except Exception:
        print("Unhandled exception during app setup.")  # TODO log exception
        raise


def main():
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(create_app())
    web.run_app(app, host=app["config"]["app"]["host"], port=app["config"]["app"]["port"])


if __name__ == "__main__":
    main()
