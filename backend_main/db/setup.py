from aiopg.sa import create_engine
from psycopg2.pool import ThreadedConnectionPool

from backend_main.db.cleanup import close_connection_pools


async def setup_connection_pools(app):
    db_config = app["config"]["db"]

    # aiopg.sa engine for database connections in main app functionality
    app["engine"] = await create_engine(
        host=db_config["db_host"], 
        port=db_config["db_port"], 
        database=db_config["db_database"].value,
        user=db_config["db_username"].value,
        password=db_config["db_password"].value
    )

    # psycopg2 connection pool with threading support for auxiallary tasks performed in separate threads 
    # (e.g. `searchables` table update)
    if app["config"]["auxillary"]["enable_searchables_updates"]:
        app["threaded_pool"] = ThreadedConnectionPool(1, 5,
            host=db_config["db_host"], 
            port=db_config["db_port"], 
            database=db_config["db_database"].value,
            user=db_config["db_username"].value,
            password=db_config["db_password"].value
        )

    # Close connection pools on cleanup
    app.on_cleanup.append(close_connection_pools)

    # TODO log connection pools acquiring
