from aiopg.sa import create_engine
# from psycopg2.pool import ThreadedConnectionPool
from aiohttp import web

from backend_main.db.cleanup import close_connection_pools
from backend_main.types import app_config_key
# TODO move to app subdir & add comments (also move `close_connection_pools`)


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
