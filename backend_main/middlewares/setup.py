from aiohttp import web
from aiohttp_remotes import ForwardedRelaxed

from backend_main.app.types import app_config_key

from backend_main.middlewares.auth import auth_middleware
from backend_main.middlewares.errors import error_middleware
from backend_main.middlewares.bounce import bounce_middleware
from backend_main.middlewares.connection import connection_middleware
from backend_main.middlewares.logging import logging_middleware
from backend_main.middlewares.tasks import tasks_middleware
# from backend_main.middlewares.threading import threading_middleware


def setup_middlewares(app: web.Application):
    use_forwarded = app[app_config_key].app.use_forwarded
    if use_forwarded:
        forwarded = ForwardedRelaxed()
        app.middlewares.append(forwarded.middleware)
    
    app.middlewares.append(logging_middleware)
    app.middlewares.append(error_middleware)
    app.middlewares.append(bounce_middleware)
    app.middlewares.append(tasks_middleware)
    # app.middlewares.append(threading_middleware)
    app.middlewares.append(connection_middleware)
    app.middlewares.append(auth_middleware)

    app["log_event"]("INFO", "app_start", "Finished setting up middlewares.", details=f"use_forwarded = {use_forwarded}")
