from asyncio import get_running_loop
import logging
from uuid import uuid4

from backend_main.logging.handlers.app import get_access_logger_handler, get_event_logger_handler


def setup_loggers(app):
    """
    Sets up access and event loggers in the app.
    """
    setup_app_access_logging(app)
    setup_app_event_logging(app)

    # Set up logger cleanup
    app.on_cleanup.append(cleanup_loggers)


async def cleanup_loggers(app):
    """
    Clean loggers on application exit.

    NOTE: function must be async to be added to `app` on_cleanup list.
    """
    if app["config"]["logging"]["app_event_log_mode"] == "file":
        app["event_logger"].handlers[0].doRollover()    # Roll the current event log file over
    
    if app["config"]["logging"]["app_access_log_mode"] == "file":
        app["access_logger"].handlers[0].doRollover()    # Roll the current access log file over


def setup_app_access_logging(app):
    """ Sets up access logger and logging function in the `app`. """
    # Set up access logger
    level = logging.INFO
    app["access_logger"] = logging.getLogger("app_access_logger")
    app["access_logger"].setLevel(level)
    
    handler = get_access_logger_handler(app["config"], level)
    if handler is not None:
        app["access_logger"].addHandler(handler)
    
    # Set up logging funciton
    def log_access(request_id, path, method, status, elapsed_time, user_id, remote, user_agent, referer):
        # Don't emit log records if logging is in `off` mode to prevent captures by pytest
        if app["config"]["logging"]["app_access_log_mode"] == "off": return

        extra = {"request_id": request_id, "path": path, "method": method, "status": status, "elapsed_time": elapsed_time, 
            "user_id": user_id, "remote": remote, "referer": referer, "user_agent": user_agent}
        app["access_logger"].log(level, "", extra=extra)
    
    app["log_access"] = log_access


def setup_app_event_logging(app):
    """ Sets up event logger and logging function in the `app`. """
    # Set up event logger
    level = logging.INFO
    app["event_logger"] = logging.getLogger("app_event_logger")
    app["event_logger"].setLevel(level)
    
    handler = get_event_logger_handler(app["config"], level)
    if handler is not None:
        app["event_logger"].addHandler(handler)
    
    # Set up logging funciton    
    def log_event(level, event_type, message, details = "", exc_info = None):
        # Don't emit log records if logging is in `off` mode to prevent captures by pytest
        if app["config"]["logging"]["app_event_log_mode"] == "off": return

        level = _get_level(level)
        extra = {"event_type": event_type, "request_id": "", "details": details}
        app["event_logger"].log(level, message, extra=extra, exc_info=exc_info)
    
    app["log_event"] = log_event


def setup_request_event_logging(request):
    """ Set up request event logging function and log-related params. """
    def log(level, event_type, message, details = "", exc_info = None):
        # Don't emit log records if logging is in `off` mode to prevent captures by pytest
        if request.config_dict["config"]["logging"]["app_event_log_mode"] == "off": return

        # Don't log CORS requests
        if request.method in ("OPTIONS", "HEAD"): return

        level = _get_level(level)
        extra = {"event_type": event_type, "request_id": request["request_id"], "details": details}
        request.config_dict["event_logger"].log(level, message, extra=extra, exc_info=exc_info)
    
    request["log_event"] = log


def _get_level(level):
    """ Converts string log level to logging.%LEVEL% enum value. """
    if type(level) == str:
        return getattr(logging, level.upper(), logging.INFO)
    return level
