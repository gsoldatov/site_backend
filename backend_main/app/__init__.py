import asyncio
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web
from psycopg2.errors import OperationalError

from backend_main.app.config import get_config, Config
from backend_main.app.cors import setup_cors
from backend_main.app.db_connection import setup_connection_pools, close_connection_pools
from backend_main.logging.loggers.app import setup_loggers, cleanup_loggers
from backend_main.middlewares import setup_middlewares

from backend_main.db.tables import get_tables
from backend_main.routes import setup_routes

from backend_main.util.connection import start_transaction

from backend_main.types.app import app_config_key, app_pending_tasks_key, \
    app_log_event_key, app_tables_key, app_can_process_requests_key, \
    app_start_transaction_key, StartTransaction


async def create_app(
        config_file: str | None = None,
        config: Config | None = None,
        start_transaction_fn: StartTransaction | None = None
    ) -> web.Application:
    try:
        app = web.Application()
        app[app_config_key] = config if type(config) == Config else get_config(config_file)
        setup_loggers(app)
        setup_middlewares(app)

        # Setup connection pool & tables
        await setup_connection_pools(app)
        app[app_tables_key] = get_tables()[0]

        # Setup async thread pool executor
        pool_size = 10  # limit pool size to 1/2 of connection pool; it may be worth moving both of these into the config file
        loop = asyncio.get_event_loop()
        loop.set_default_executor(ThreadPoolExecutor(pool_size))    # NOTE: ThreadPoolExecutor is used by default,
                                                                    # so only the number of workers is adjusted here
        
        # Setup transaction starting function
        app[app_start_transaction_key] = start_transaction_fn if start_transaction_fn is not None else start_transaction

        # Create a storage for running tasks references to avoid them
        # being destroyed by the garbage collector before they complete
        app[app_pending_tasks_key] = set()
        
        # Set flag for request bounce middleware
        app[app_can_process_requests_key] = { "value": True }   # type: ignore[misc]

        # Setup routes
        setup_routes(app)
        setup_cors(app)

        app[app_log_event_key]("INFO", "app_start", "Finished app setup.")

        return app
    
    except OperationalError:
        app[app_log_event_key]("CRITICAL", "app_start", "Failed to setup database connection pools.")
        raise web.GracefulExit()    # Close the app gracefully
    
    except Exception:
        try:
            app[app_log_event_key]("CRITICAL", "app_start", "Unhandled exception during app setup.", exc_info=True)
        except KeyError:
            pass
        await close_connection_pools(app)   # Ensure connection pools and loggers are cleaned up
        await cleanup_loggers(app)
        raise
