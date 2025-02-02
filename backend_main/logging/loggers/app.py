import logging
from aiohttp import web
import json
from typing import cast, Any

from backend_main.logging.handlers.app import get_access_logger_handler, get_event_logger_handler
from backend_main.logging.handlers.patched_timed_rotation_file_handler import PatchedTimedRotatingFileHandler

from backend_main.types.app import app_config_key, app_event_logger_key, app_access_logger_key, \
    app_log_access_key, app_log_event_key
from backend_main.types.request import Request, request_id_key, request_log_event_key



def setup_loggers(app: web.Application) -> None:
    """
    Sets up access and event loggers in the app.
    """
    setup_app_access_logging(app)
    setup_app_event_logging(app)

    # Set up logger cleanup
    app.on_cleanup.append(cleanup_loggers)


async def cleanup_loggers(app: web.Application) -> None:
    """
    Clean loggers on application exit.

    NOTE: function must be async to be added to `app` on_cleanup list.
    """
    if app_config_key in app:
        if app[app_config_key].logging.app_event_log_mode == "file" and app_event_logger_key in app:
            h = cast(PatchedTimedRotatingFileHandler, app[app_event_logger_key].handlers[0])
            h.doRollover()    # Roll the current event log file over
        
        if app[app_config_key].logging.app_access_log_mode == "file" and app_access_logger_key in app:
            h = cast(PatchedTimedRotatingFileHandler, app[app_access_logger_key].handlers[0])
            h.doRollover()    # Roll the current access log file over


def setup_app_access_logging(app: web.Application) -> None:
    """ Sets up access logger and logging function in the `app`. """
    # Set up access logger
    level = logging.INFO
    app[app_access_logger_key] = logging.getLogger("app_access_logger")
    app[app_access_logger_key].setLevel(level)
    
    handler = get_access_logger_handler(app[app_config_key], level)
    if handler is not None:
        app[app_access_logger_key].addHandler(handler)
    
    # Set up logging funciton
    def log_access(
        request_id: str,
        path: str,
        method: str,
        status: int,
        elapsed_time: float,
        user_id: int | str,
        remote: str | None,
        user_agent: str,
        referer: str
    ) -> None:
        # Don't emit log records if logging is in `off` mode to prevent captures by pytest
        if app[app_config_key].logging.app_access_log_mode == "off": return

        extra = {"request_id": request_id, "path": path, "method": method, "status": status, "elapsed_time": elapsed_time, 
            "user_id": user_id, "remote": remote, "referer": referer, "user_agent": user_agent}
        app[app_access_logger_key].log(level, "", extra=extra)
    
    app[app_log_access_key] = log_access


def setup_app_event_logging(app: web.Application) -> None:
    """ Sets up event logger and logging function in the `app`. """
    # Set up event logger
    level = logging.INFO
    app[app_event_logger_key] = logging.getLogger("app_event_logger")
    app[app_event_logger_key].setLevel(level)
    
    handler = get_event_logger_handler(app[app_config_key], level)
    if handler is not None:
        app[app_event_logger_key].addHandler(handler)
    
    # Set up logging funciton    
    def log_event(
            str_level: str,
            event_type: str,
            message: str,
            details: dict[str, Any] | str = "",
            exc_info: bool | None = None
        ) -> None:
        # Don't emit log records if logging is in `off` mode to prevent captures by pytest
        if app[app_config_key].logging.app_event_log_mode == "off": return

        level = _get_level(str_level)
        if isinstance(details, dict): details = json.dumps(details)
        extra = {"event_type": event_type, "request_id": "", "details": details}
        app[app_event_logger_key].log(level, message, extra=extra, exc_info=exc_info)
    
    app[app_log_event_key] = log_event


def setup_request_event_logging(request: Request) -> None:
    """ Set up request event logging function and log-related params. """
    def log(
        str_level: str,
        event_type: str,
        message: str,
        details: dict[str, Any] | str = "",
        exc_info: bool | None = None
    ) -> None:
        # Don't emit log records if logging is in `off` mode to prevent captures by pytest
        if request.config_dict[app_config_key].logging.app_event_log_mode == "off": return

        # Don't log CORS requests
        if request.method in ("OPTIONS", "HEAD"): return

        level = _get_level(str_level)
        if isinstance(details, dict): details = json.dumps(details)
        extra = {"event_type": event_type, "request_id": request[request_id_key], "details": details}
        request.config_dict[app_event_logger_key].log(level, message, extra=extra, exc_info=exc_info)
    
    request[request_log_event_key] = log


def _get_level(level: str | int) -> int:
    """ Converts string log level to logging.%LEVEL% enum value. """
    if isinstance(level, str):
        return getattr(logging, level.upper(), logging.INFO)
    return level
