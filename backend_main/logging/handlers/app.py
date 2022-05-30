import os
import logging

from backend_main.logging.handlers.file_handler import get_file_handler
from backend_main.logging.handlers.stream import get_stream_handler
from backend_main.logging.formatters.multiline import MultilineFormatter


# root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def get_event_logger_handler(config, level):
    # TODO docstring
    app_event_log_mode = config["logging"]["app_event_log_mode"]

    if app_event_log_mode == "file":
        raise NotImplementedError()
    
    elif app_event_log_mode == "stdout":
        # fmt = " ".join(["%(asctime)s", "%(levelname)s", "%(event_type)s", "%(request_id)s", "%(message)s", "%(details)s"])
        fmt = " ".join(["%(levelname)s", "%(event_type)s", "%(request_id)s", "%(message)s", "%(details)s"])
        formatter = logging.Formatter(fmt)
        return get_stream_handler(level, formatter)
    
    return None
