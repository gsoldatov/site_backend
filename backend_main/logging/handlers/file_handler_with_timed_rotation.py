from logging import Formatter
import os

from backend_main.logging.handlers.patched_timed_rotation_file_handler import PatchedTimedRotatingFileHandler


def get_file_handler_with_timed_rotation(
        folder: str,
        name: str,
        level: int,
        formatter: Formatter,
        interval: int = 24 * 60 * 60
    ):
    """
    Returns a FileHandler instance.
    `folder` is the asbolute path to the log (created if missing).
    `name` is the first part of log file (fullname is {name}_{curr_timestamp}.log").
    `level` is the log level of the handler.
    `formatter` is a logging.Formatter instance used for log record formatting;
    `interval` is the period between file rotation in seconds (defaults to 24 hours).
    """
    # Ensure folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    # Get log file name (without time suffix)
    filename = os.path.join(folder, f"{name}")

    # Create and return handler
    handler = PatchedTimedRotatingFileHandler(filename, when="S", interval=interval, encoding="UTF-8", delay=True)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    return handler
