"""
    Logging middleware.
"""
from aiohttp import web

from backend_main.logging.loggers.app import setup_request_event_logging


@web.middleware
async def logging_middleware(request, handler):
    # Setup request event logging function
    setup_request_event_logging(request)

    try:
        request.log_event("INFO", "request", f"Processing request to {request.rel_url}.")
        response = await handler(request)
        status = response.status
        return response

    except Exception as e:
        # All excepted exceptions were wrapped in error middleware
        status = e.status_code if isinstance(e, web.HTTPException) else 500
        raise

    finally:
        remote = request.remote
        path = request.path
        method = request.method
        elapsed_time = round(request.loop.time() - request["start_time"], 3)
        user_agent = request.headers.get("User-Agent", "")
        referer = request.headers.get("Referer", "")

        request.log_event("INFO", "request", "Finished processing request.", details=f"status = ${status}")

        # Don't log CORS requests
        if request.method not in ("OPTIONS", "HEAD"):
            request.app.log_access(remote, path, method, status, elapsed_time, user_agent, referer)