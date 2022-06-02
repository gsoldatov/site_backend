import os
import logging

from backend_main.logging.handlers.file_handler import get_file_handler
from backend_main.logging.handlers.stream import get_stream_handler
from backend_main.logging.formatters.multiline import MultilineFormatter


root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def get_handler(name, config, level):
    """
    Returns a handler based on the `config` settings with the provided log `level`.
    Possible options, based on config > logging > db_mode setting:
    - `file` => FileHandler, which writes into config > logging > folder;
    - `stdout` => StreamHandler, which writes to stdout;
    - `off` => no handler is returned.
    """
    db_mode = config["logging"]["scheduled_mode"]
    delimiter = ";" if db_mode == "file" else " "

    if db_mode == "file":
        # Log folder (can be absolute or relative to project root folder)
        folder = config["logging"]["folder"] if os.path.isabs(config["logging"]["folder"]) \
            else os.path.abspath(os.path.join(root_folder, config["logging"]["folder"]))
        
        # Formatter instance
        fmt = delimiter.join(["%(asctime)s", "%(levelname)s", "%(message)s"])
        formatter = MultilineFormatter(fmt)

        # Create and return handler
        _file_handler = get_file_handler(folder, name, level, formatter)
        return _file_handler
    
    elif db_mode == "stdout":
        fmt = delimiter.join(["%(levelname)s", "%(message)s"])
        formatter = logging.Formatter(fmt)
        return get_stream_handler(level, formatter)
    
    return None
