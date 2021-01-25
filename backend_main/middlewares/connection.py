"""
    Database connection handling middleware.
"""
from aiohttp import web


@web.middleware
async def connection_middleware(request, handler):
    async with request.app["engine"].acquire() as conn:
        request["conn"] = conn
        trans = await conn.begin()
        try:
            result = await handler(request)
            await trans.commit()
            return result

        except Exception as e:
            await trans.rollback()
            raise e
