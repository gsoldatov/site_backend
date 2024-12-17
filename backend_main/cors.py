import aiohttp_cors # type: ignore


def setup_cors(app):
    resource_options = aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
    
    cors = aiohttp_cors.setup(app, defaults = {
        url: resource_options for url in app["config"]["cors_urls"]
    })

    for route in app.router.routes():
        cors.add(route)
