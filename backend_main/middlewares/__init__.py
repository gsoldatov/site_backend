from aiohttp import web
from aiohttp_remotes import ForwardedRelaxed

from backend_main.middlewares.auth import auth_middleware
from backend_main.middlewares.errors import error_middleware
from backend_main.middlewares.bounce import bounce_middleware
from backend_main.middlewares.connection import connection_middleware
from backend_main.middlewares.logging import logging_middleware
from backend_main.middlewares.tasks import tasks_middleware
# from backend_main.middlewares.threading import threading_middleware

from backend_main.types.app import app_config_key, app_log_event_key


def setup_middlewares(app: web.Application):
    use_forwarded = app[app_config_key].app.use_forwarded
    if use_forwarded:
        forwarded = ForwardedRelaxed()
        app.middlewares.append(forwarded.middleware)
    
    for middleware in [
        logging_middleware,
        error_middleware,
        bounce_middleware,
        tasks_middleware,
        # threading_middleware,
        connection_middleware,
        auth_middleware
    ]:
        app.middlewares.append(middleware)  # type: ignore[arg-type]

    app[app_log_event_key]("INFO", "app_start", "Finished setting up middlewares.", details=f"use_forwarded = {use_forwarded}")
