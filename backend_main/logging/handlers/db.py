import os, sys
from datetime import datetime
import logging

root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend_main.logging.formatters.db import file_db_formatter, stdout_db_formatter


def get_handler(config, level):
    """ 
    Returns an appropriate handler, based on the `config` > logging > db_mode value. 
    If logging is disabled, returns None.

    Returns the same object in each subsequent excecution, which ensures that file handler 
    writes into the same file throughout the run of the db utility.
    """
    db_mode = config["logging"]["db_mode"]

    if db_mode == "file":
        return _get_singleton_file_handler(config, level)
    elif db_mode == "stdout":
        return _get_singleton_stream_handler(level)
    else:
        return None


def _get_singleton_file_handler(config, level):
    """ 
    Singleton, which produces and returns a `FileHandler`, which writes into
    the specified inside `config` folder.
    """
    global _file_handler

    if _file_handler is None:
        # Get log folder and create if it doesn't exist
        log_folder = config["logging"]["folder"] if os.path.isabs(config["logging"]["folder"]) \
            else os.path.abspath(os.path.join(root_folder, config["logging"]["folder"]))
        
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        
        # Get log file name
        timestamp = datetime.strftime(datetime.now(), "%Y_%m_%d_%H_%M_%S")
        filename = os.path.join(log_folder, f"db_module_{timestamp}.log")

        # Initialize and set handler
        _file_handler = logging.FileHandler(filename, encoding="utf-8")
        _file_handler.setFormatter(file_db_formatter)
        _file_handler.setLevel(level)

    return _file_handler


def _get_singleton_stream_handler(level):
    """ 
    Singleton, which produces and returns a `StreamHandler`, which writes into
    the specified inside `config` folder.
    """
    global _stream_handler

    if _stream_handler is None:
        _stream_handler = logging.StreamHandler(sys.stdout)
        _stream_handler.setLevel(level)
        _stream_handler.setFormatter(stdout_db_formatter)

    return _stream_handler


_file_handler = None
_stream_handler = None
