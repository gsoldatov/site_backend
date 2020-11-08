"""
Validation utility functions.
"""
from datetime import datetime
from urllib.parse import urlparse
import json


def validate_link(link):
    """
    Checks if provided string is a valid URL and raises a LinkValidationException if it isn't.
    """
    result = urlparse(link)
    if not result.scheme or not result.netloc:
        raise LinkValidationException("Provided string is not a valid URL")


class BaseException(Exception):
    def __init__(self, message):
        self.message = message


class LinkValidationException(BaseException):
    pass
    
class ObjectsTagsUpdateException(BaseException):
    pass
