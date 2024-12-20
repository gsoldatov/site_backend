import sys
import logging

from typing import TextIO


def get_stream_handler(level: int, formatter: logging.Formatter, stream: TextIO = sys.stdout):
    """ 
    Returns a StreamHandler instance with the specified log `level` and `formatter`.
    `stream` can be provided as well (if not, defaults to stdout).
    """
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    return handler
