"""
    Logging middleware.
"""
from asyncio import get_running_loop
from aiohttp import web
from datetime import datetime, timezone
from uuid import uuid4

from backend_main.logging.loggers.app import setup_request_event_logging

from backend_main.types.app import app_log_access_key
from backend_main.types.request import Request, Handler, request_time_key, request_id_key, \
    request_monotonic_time_key, request_log_event_key, request_user_info_key


@web.middleware
async def logging_middleware(request: Request, handler: Handler) -> web.Response:
    # Set request id & time
    request[request_time_key] = datetime.now(tz=timezone.utc)     # Request start time
    request[request_id_key] = str(uuid4())[:8]
    request[request_monotonic_time_key] = get_running_loop().time()     # Monotonic time from loop timer for measuring elapsed time

    # Setup request event logging function
    setup_request_event_logging(request)

    try:
        request[request_log_event_key]("INFO", "request", f"Processing request to {request.rel_url}.")
        response = await handler(request)
        status = response.status
        return response

    except Exception as e:
        # All expected exceptions were processed in error middleware
        status = e.status_code if isinstance(e, web.HTTPException) else 500
        raise

    finally:
        request_id = request[request_id_key]
        path = request.path
        method = request.method
        elapsed_time = round(get_running_loop().time() - request[request_monotonic_time_key], 3)
        
        user_id: str | int = "anonymous"
        if request_user_info_key in request:
            if (ui_user_id := request[request_user_info_key].user_id) is not None: user_id = ui_user_id

        remote = request.remote
        user_agent = request.headers.get("User-Agent", "")
        referer = request.headers.get("Referer", "")

        request[request_log_event_key]("INFO", "request", "Finished processing request.", details={"status": status})

        # Don't log CORS requests
        if request.method not in ("OPTIONS", "HEAD"):
            request.config_dict[app_log_access_key](
                request_id, path, method, status, elapsed_time, user_id, remote, user_agent, referer
            )
