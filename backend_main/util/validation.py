"""
Validation utility functions.
"""
from datetime import datetime
from urllib.parse import urlparse
import json
from collections import Counter


def validate_link(link):
    """
    Checks if provided string is a valid URL and raises a LinkValidationException if it isn't.
    """
    result = urlparse(link)
    if not result.scheme or not result.netloc:
        raise LinkValidationException("Provided string is not a valid URL")


def validate_to_do_list(items):
    """
        Checks if item numbers are unique.
    """
    c = Counter((i["item_number"] for i in items))
    non_unique_item_numbers = [n for n in c if c[n] > 1]
    if len(non_unique_item_numbers) > 0:
        raise To_Do_Lists_ValidationException(f"Received non-unique item numbers {non_unique_item_numbers} when adding or updating a to-do list.")


class BaseException(Exception):
    def __init__(self, message):
        self.message = message


class LinkValidationException(BaseException):
    pass

class To_Do_Lists_ValidationException(BaseException):
    pass
    
class ObjectsTagsUpdateException(BaseException):
    pass
