import asyncio

from aiohttp import web
from aiopg.sa import create_engine

from backend_main.app.types import app_config_key


async def setup_connection_pools(app: web.Application):
    db_config = app[app_config_key].db

    # aiopg.sa engine for database connections in main app functionality
    app["engine"] = await create_engine(
        maxsize=20,
        host=db_config.db_host, 
        port=db_config.db_port, 
        database=db_config.db_database.value,
        user=db_config.db_username.value,
        password=db_config.db_password.value
    )
    app["log_event"]("INFO", "app_start", "Created main connection pool.")


    # # psycopg2 connection pool with threading support for auxiallary tasks performed in separate threads 
    # # (e.g. `searchables` table update)
    # # NOTE: updating searchables in a separate thread 
    # if app[app_config_key].auxillary.enable_searchables_updates:
    #     app["threaded_pool"] = ThreadedConnectionPool(1, 5,
    #         host=db_config.db_host, 
    #         port=db_config.db_port, 
    #         database=db_config.db_database.value,
    #         user=db_config.db_username.value,
    #         password=db_config.db_password.value
    #     )
    #     app["log_event"]("INFO", "app_start", "Created threaded connection pool.")

    # Close connection pools on cleanup
    app.on_cleanup.append(close_connection_pools)


async def close_connection_pools(app: web.Application):
    # Disable request processing
    app["can_process_requests"]["value"] = False

    # Wait for searchable update tasks to complete
    if app[app_config_key].auxillary.enable_searchables_updates:
        while len(app["pending_tasks"]) > 0:
            await asyncio.sleep(0.1)
    
    # Close connection pool
    if "engine" in app:
        app["engine"].close()
        await app["engine"].wait_closed()
        app["log_event"]("INFO", "app_cleanup", "Closed main connection pool.")

    # NOTE: Threaded connection pool is no longer used
    # if "threaded_pool" in app:
    #     app["threaded_pool"].closeall()
    #     app["log_event"]("INFO", "app_cleanup", "Closed threaded connection pool.")
    
    return app
