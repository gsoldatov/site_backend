from aiohttp import web
from aiopg.sa import create_engine

from config import get_config
from db.cleanup import close_engine
from db.tables import get_tables
from routes import setup_routes


async def create_app(config_file = None, config = None):
    app = web.Application()
    app["config"] = config if config and type(config) == dict else get_config(config_file)

    db_config = app["config"]["db"]
    app["engine"] = await create_engine(host = db_config["db_host"], 
                                  port = db_config["db_port"], 
                                  database = db_config["db_database"],
                                  user = db_config["db_username"],
                                  password = db_config["db_password"]
                                  )
    app.on_cleanup.append(close_engine)

    app["tables"] = get_tables(app["config"])
    setup_routes(app)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app)
