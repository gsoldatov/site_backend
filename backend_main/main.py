if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(sys.path[0]))

import asyncio
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web
from psycopg2.errors import OperationalError

from backend_main.config import get_config
from backend_main.cors import setup_cors
from backend_main.db.setup import setup_connection_pools
from backend_main.db.cleanup import close_connection_pools
from backend_main.logging.loggers.app import setup_loggers, cleanup_loggers
from backend_main.middlewares.setup import setup_middlewares

from backend_main.db.tables import get_tables
from backend_main.routes import setup_routes


async def create_app(config_file = None, config = None):
    try:
        app = web.Application()
        app["config"] = config if config and type(config) == dict else get_config(config_file)
        setup_loggers(app)
        setup_middlewares(app)

        # Setup connection pool & tables
        await setup_connection_pools(app)
        app["tables"] = get_tables()[0]

        # Setup async thread pool executor
        if app["config"]["auxillary"]["enable_searchables_updates"]:
            loop = asyncio.get_event_loop()
            loop.set_default_executor(ThreadPoolExecutor(10))   # NOTE: pool size is limited to 1/2 of connection pool;
                                                                # may be worth moving both of these into the config file
            # Create a storage for running tasks references to avoid them
            # being destroyed by the garbage collector before they complete
            app["pending_tasks"] = set()
        
        # Set flag for request bounce middleware 
        # NOTE: dict is used to avoid warnings about state change of a frozen app
        app["can_process_requests"] = { "value": True } 

        # Setup routes
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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = loop.run_until_complete(create_app())
    web.run_app(app, host=app["config"]["app"]["host"], port=app["config"]["app"]["port"], loop=loop)


if __name__ == "__main__":
    main()
