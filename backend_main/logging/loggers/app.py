import logging
from uuid import uuid4

from backend_main.logging.handlers.app import get_event_logger_handler


def setup_loggers(app):
    """
    Sets up access and event loggers in the app.
    """
    # Setup application event logging
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


def setup_app_event_logging(app):
    """ Sets up event logger and logging function in the `app`. """
    # Set up event logger
    level = logging.INFO
    delimiter = ";" if app["config"]["logging"]["app_event_log_mode"] == "file" else " "
    app["event_logger"] = logging.getLogger("backend")
    app["event_logger"].setLevel(level)
    
    handler = get_event_logger_handler(app["config"], level, delimiter)
    if handler is not None:
        app["event_logger"].addHandler(handler)
    
    # Set up logging funciton    
    def log(level, event_type, message, details = "", exc_info = None):
        # Don't emit log records if logging is in `off` mode to prevent captures by pytest
        if app["config"]["logging"]["app_event_log_mode"] == "off": return

        level = _get_level(level)
        extra = {"event_type": event_type, "request_id": "", "details": details.replace("\n", " ")}
        app["event_logger"].log(level, message, extra=extra, exc_info=exc_info)
    
    app.log_event = log


def setup_request_event_logging(request):
    """ Set up request event logging function and log-related params. """
    def log(level, event_type, message, details = "", exc_info = None):
        # Don't emit log records if logging is in `off` mode to prevent captures by pytest
        if request.config_dict["config"]["logging"]["app_event_log_mode"] == "off": return

        # Don't log CORS requests
        if request.method in ("OPTIONS", "HEAD"): return

        level = _get_level(level)
        extra = {"event_type": event_type, "request_id": request["request_id"], "details": details.replace("\n", " ")}
        request.config_dict["event_logger"].log(level, message, extra=extra, exc_info=exc_info)
    
    request["request_id"] = str(uuid4())[:8]
    request.log_event = log


def _get_level(level):
    """ Converts string log level to logging.%LEVEL% enum value. """
    if type(level) == str:
        return getattr(logging, level.upper(), logging.INFO)
    return level





    
    



# def log(level, message, extra = None):
    # event_type, request_id, "%(remote)s", "%(message)s", "%(details)s"

    # fmt = " ".join(["%(asctime)s", "%(level)s", "%(event_type)s", "%(request_id)s", "%(remote)s", "%(message)s", "%(details)s"])
