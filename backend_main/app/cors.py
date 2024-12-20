import aiohttp_cors # type: ignore[import-untyped]

from aiohttp import web

from backend_main.app.types import app_config_key


def setup_cors(app: web.Application):
    resource_options = aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
    
    cors = aiohttp_cors.setup(app, defaults = {
        url: resource_options for url in app[app_config_key].cors_urls
    })

    for route in app.router.routes():
        cors.add(route)
