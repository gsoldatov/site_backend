"""
    Middleware for handling asynchronous connection pooling & transaction completion.
"""
from aiohttp import web

from backend_main.util.exceptions import IncorrectCredentialsException
from backend_main.util.json import error_json

from backend_main.types.app import app_engine_key
from backend_main.types.request import Request, Handler, request_connection_key, request_transaction_key


@web.middleware
async def connection_middleware(request: Request, handler: Handler) -> web.Response:
    # Skip middleware for CORS requests
    if request.method in ("OPTIONS", "HEAD"): return await handler(request)
    
    async with request.config_dict[app_engine_key].acquire() as conn:
        request[request_connection_key] = conn
        
        try:
            result = await handler(request)
            if request.get(request_transaction_key) is not None: await request[request_transaction_key].commit()
            return result
        
        # Commit login rate limiting information
        except IncorrectCredentialsException as e:
            if request.get(request_transaction_key) is not None: await request[request_transaction_key].commit()
            raise web.HTTPUnauthorized(text=error_json(e.msg), content_type="application/json")

        except Exception as e:
            if request.get(request_transaction_key) is not None: await request[request_transaction_key].rollback()
            request.pop("searchable_updates_tag_ids", None)
            request.pop("searchable_updates_object_ids", None)
            raise e
