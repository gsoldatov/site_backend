import logging

from backend_main.app.types import Config

from backend_main.logging.handlers.db import get_handler


def get_logger(
        name: str,
        config: Config,
        level: int = logging.DEBUG
    ):
    """
    Returns a new logger with the specified `name`.
    Writes messages to a file or stdout, based on the config settings.
    """
    # Create logger with a specified name
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Set handler based on the logging mode
    handler = get_handler(config, level)
    if handler is not None:
        logger.addHandler(handler)
    
    # Return logger
    return logger
