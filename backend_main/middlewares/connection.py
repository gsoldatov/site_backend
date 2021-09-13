"""
    Database connection handling middleware.
"""
from aiohttp import web

from backend_main.util.login_rate_limits import IncorrectCredentialsException
from backend_main.util.json import error_json


@web.middleware
async def connection_middleware(request, handler):
    async with request.app["engine"].acquire() as conn:
        request["conn"] = conn
        trans = await conn.begin()
        try:
            result = await handler(request)
            await trans.commit()
            return result
        
        # Commit login rate limiting information
        except IncorrectCredentialsException as e:
            await trans.commit()
            raise web.HTTPUnauthorized(text=error_json("Incorrect login or password."), content_type="application/json")

        except Exception as e:
            await trans.rollback()
            raise e
