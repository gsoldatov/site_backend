if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(sys.path[0]))

import asyncio
from sys import exc_info

from aiohttp import web
from psycopg2.errors import OperationalError

from backend_main.config import get_config
from backend_main.cors import setup_cors
from backend_main.db.setup import setup_connection_pools
from backend_main.db.cleanup import close_connection_pools
from backend_main.logging.loggers.app import setup_loggers, cleanup_loggers
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

        setup_loggers(app)
        
        await setup_connection_pools(app)
        
        app["tables"] = get_tables()[0]

        setup_routes(app)
        
        setup_cors(app)

        app.log_event("INFO", "app_start", "Finished app setup.")
        return app
    
    except OperationalError:
        app.log_event("CRITICAL", "app_start", "Failed to setup database connection pools.")
        raise web.GracefulExit()    # Close the app gracefully
    
    except Exception:
        if getattr(app, "log_event", None):
            app.log_event("CRITICAL", "app_start", "Unhandled exception during app setup.", exc_info=True)
        await close_connection_pools(app)   # Ensure connection pools and loggers are cleaned up
        await cleanup_loggers(app)
        raise


def main():
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(create_app())
    web.run_app(app, host=app["config"]["app"]["host"], port=app["config"]["app"]["port"])


if __name__ == "__main__":
    main()
