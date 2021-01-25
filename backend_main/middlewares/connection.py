"""
    Database connection handling middleware.
"""
from aiohttp import web


@web.middleware
async def connection_middleware(request, handler):
    async with request.app["engine"].acquire() as conn:
        request["conn"] = conn
        return await handler(request)
