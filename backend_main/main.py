if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(sys.path[0]))

from aiohttp import web
from aiopg.sa import create_engine

from backend_main.config import get_config
from backend_main.cors import setup_cors
from backend_main.db.cleanup import close_engine
from backend_main.db.tables import get_tables
from backend_main.routes import setup_routes


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
    setup_cors(app)

    return app


def main():
    app = create_app()
    config = get_config()
    web.run_app(app, host = config["app"]["host"], port = config["app"]["port"])


if __name__ == "__main__":
    main()
