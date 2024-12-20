from logging import Formatter
import os
from datetime import datetime
import logging


def get_file_handler(
        folder: str,
        name: str,
        level: int,
        formatter: Formatter
    ):
    """
    Returns a FileHandler instance.
    `folder` is the asbolute path to the log (created if missing).
    `name` is the first part of log file (fullname is {name}_{curr_timestamp}.log").
    `level` is the log level of the handler.
    `formatter` is a logging.Formatter instance used for log record formatting.
    """
    # Ensure folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    # Get log file name
    timestamp = datetime.strftime(datetime.now(), "%Y_%m_%d_%H_%M_%S")
    filename = os.path.join(folder, f"{name}_{timestamp}.log")

    # Create and return handler
    handler = logging.FileHandler(filename, encoding="utf-8")
    handler.setFormatter(formatter)
    handler.setLevel(level)

    return handler
