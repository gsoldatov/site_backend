if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(sys.path[0]))

import asyncio

from aiohttp import web

from backend_main.app import create_app
from backend_main.app.types import app_config_key


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = loop.run_until_complete(create_app())
    web.run_app(app, host=app[app_config_key].app.host, port=app[app_config_key].app.port, loop=loop)


if __name__ == "__main__":
    main()
