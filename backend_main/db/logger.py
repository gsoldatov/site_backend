import os, sys
from datetime import datetime
import logging
import logging.handlers

PROJECT_ROOT_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def get_logger(name, config):
    # Create logger with a specified name
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Set handler based on the logging mode
    handler = get_handler(config)
    if handler is not None:
        logger.addHandler(handler)
    
    # Return logger
    return logger


def get_handler(config):
    """ 
    Returns an appropriate handler, based on the `config` > logging > db_mode value. 
    If logging is disabled, returns None.
    """
    db_mode = config["logging"]["db_mode"]

    if db_mode == "file":
        return _get_singleton_file_handler(config)
    elif db_mode == "stdout":
        return _get_singleton_stream_handler()
    else:
        return None


def _get_singleton_file_handler(config):
    """ 
    Singleton, which produces and returns a `FileHandler`, which writes into
    the specified inside `config` folder.
    """
    global _file_handler

    if _file_handler is None:
        # Get log folder and create if it doesn't exist
        log_folder = config["logging"]["folder"] if os.path.isabs(config["logging"]["folder"]) \
            else os.path.abspath(os.path.join(PROJECT_ROOT_FOLDER, config["logging"]["folder"]))
        
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        
        # Get log file name
        timestamp = datetime.strftime(datetime.now(), "%Y_%m_%d_%H_%M_%S")
        filename = os.path.join(log_folder, f"db_module_{timestamp}.log")

        # Initialize and set handler
        _file_handler = logging.FileHandler(filename, encoding="utf-8")
        _file_handler.setFormatter(_formatter)

    return _file_handler


def _get_singleton_stream_handler():
    """ 
    Singleton, which produces and returns a `StreamHandler`, which writes into
    the specified inside `config` folder.
    """
    global _stream_handler

    if _stream_handler is None:
        _stream_handler = logging.StreamHandler(sys.stdout)
        _stream_handler.setLevel(logging.DEBUG)
        _stream_handler.setFormatter(_formatter)

    return _stream_handler


_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
_file_handler = None
_stream_handler = None
