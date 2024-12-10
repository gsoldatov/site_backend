"""
    Logging middleware.
"""
from asyncio import get_running_loop
from aiohttp import web
from datetime import datetime, timezone

from backend_main.logging.loggers.app import setup_request_event_logging


@web.middleware
async def logging_middleware(request, handler):
    # Set request time
    request["time"] = datetime.now(tz=timezone.utc)     # Request start time

    # Setup request event logging function
    setup_request_event_logging(request)

    try:
        request["log_event"]("INFO", "request", f"Processing request to {request.rel_url}.")
        response = await handler(request)
        status = response.status
        return response

    except Exception as e:
        # All excepted exceptions were wrapped in error middleware
        status = e.status_code if isinstance(e, web.HTTPException) else 500
        raise

    finally:
        request_id = request["request_id"]
        path = request.path
        method = request.method
        elapsed_time = round(get_running_loop().time() - request["monotonic_start_time"], 3)
        
        user_id = "anonymous"
        if hasattr(request, "user_info"):
            if request["user_info"].user_id: user_id = request["user_info"].user_id

        remote = request.remote
        user_agent = request.headers.get("User-Agent", "")
        referer = request.headers.get("Referer", "")

        request["log_event"]("INFO", "request", "Finished processing request.", details=f"status = {status}")

        # Don't log CORS requests
        if request.method not in ("OPTIONS", "HEAD"):
            request.app.log_access(request_id, path, method, status, elapsed_time, user_id, remote, user_agent, referer)