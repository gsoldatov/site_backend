"""
    Middleware for handling asynchronous connection pooling & transaction completion.

    NOTE: threaded_pool connections are being dispatched in `threading` middleware.
"""
from aiohttp import web

from backend_main.util.login_rate_limits import IncorrectCredentialsException
from backend_main.util.json import error_json


@web.middleware
async def connection_middleware(request, handler):
    # Skip middleware for CORS requests
    if request.method in ("OPTIONS", "HEAD"): return await handler(request)
    
    async with request.config_dict["engine"].acquire() as conn:
        request["conn"] = conn
        
        try:
            result = await handler(request)
            if request.get("trans") is not None: await request["trans"].commit()
            return result
        
        # Commit login rate limiting information
        except IncorrectCredentialsException as e:
            if request.get("trans") is not None: await request["trans"].commit()
            raise web.HTTPUnauthorized(text=error_json("Incorrect login or password."), content_type="application/json")

        except Exception as e:
            if request.get("trans") is not None: await request["trans"].rollback()
            request.pop("searchable_updates_tag_ids", None)
            request.pop("searchable_updates_object_ids", None)
            raise e


async def start_transaction(request):
    """ Starts a transaction and adds it to request, if there is currently no active transaction in `request` storage. """
    if "trans" in request:
        if request["trans"].is_active:
            return
    
    request["trans"] = await request["conn"].begin()
