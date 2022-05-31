import os
import logging

from backend_main.logging.handlers.file_handler_with_timed_rotation import get_file_handler_with_timed_rotation
from backend_main.logging.handlers.stream import get_stream_handler
from backend_main.logging.formatters.multiline import MultilineFormatter


root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def get_event_logger_handler(config, level, delimiter):
    """
    Returns a handler based on the `config` settings with the provided log `level`.
    Possible options, based on config > logging > app_event_log_mode setting:
    - `file` => TimedRotatingFileHandler, which writes into config > logging > folder;
    - `stdout` => StreamHandler, which writes to stdout;
    - `off` => no handler is returned.
    """
    app_event_log_mode = config["logging"]["app_event_log_mode"]

    if app_event_log_mode == "file":
        # Log folder (can be absolute or relative to project root folder)
        folder = config["logging"]["folder"] if os.path.isabs(config["logging"]["folder"]) \
        else os.path.abspath(os.path.join(root_folder, config["logging"]["folder"]))

        # Formatter
        fmt = delimiter.join(["%(asctime)s", "%(request_id)s", "%(levelname)s", "%(event_type)s", "%(message)s", "%(details)s"])
        formatter = MultilineFormatter(fmt)


        return get_file_handler_with_timed_rotation(folder, "app_event_log", level, formatter)
    
    elif app_event_log_mode == "stdout":
        fmt = delimiter.join(["%(request_id)s", "%(levelname)s", "%(event_type)s", "%(message)s", "%(details)s"])
        formatter = logging.Formatter(fmt)
        return get_stream_handler(level, formatter)
    
    return None
