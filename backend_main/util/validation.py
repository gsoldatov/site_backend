"""
Validation utility functions.
"""
from datetime import datetime
from urllib.parse import urlparse
import json
from collections import Counter


def validate_link(link):
    """ Checks if provided string is a valid URL and raises a RequestValidationException if it isn't. """
    result = urlparse(link)
    if not result.scheme or not result.netloc:
        raise RequestValidationException("Provided string is not a valid URL")


def validate_to_do_list(items):
    """ Checks if item numbers are unique. """
    c = Counter((i["item_number"] for i in items))
    non_unique_item_numbers = [n for n in c if c[n] > 1]
    if len(non_unique_item_numbers) > 0:
        raise RequestValidationException(f"Received non-unique item numbers {non_unique_item_numbers} when adding or updating a to-do list.")


def validate_composite(object_id_and_data):
    """ Additional validation for composite object data. """
    object_id, object_data = object_id_and_data["object_id"], object_id_and_data["object_data"]

    # Subobjects IDs are unique
    subobject_ids = []
    for so in object_data["subobjects"]:
        so_id = so["object_id"]
        if so_id in subobject_ids:
            raise RequestValidationException(f"Validation error for composite object ID `{object_id}`, subobject ID `{so_id}` is not unique.")
        else:
            subobject_ids.append(so_id)

    # Row + column combinations must be unique among all subobjects
    subobject_positions = []
    for so in object_data["subobjects"]:
        so_id = so["object_id"]
        so_pos = (so["row"], so["column"])
        if so_pos in subobject_positions:
            raise RequestValidationException(f"Validation error for composite object ID `{object_id}`, position `{so_pos}` of subobject `{so_id}` is not unique.")
        else:
            subobject_positions.append(so_pos)
    
    # Deleted subobjects can't remain in subobjects list
    deleted_ids = [so["object_id"] for so in object_data["deleted_subobjects"]]
    intersection = set(subobject_ids).intersection(set(deleted_ids))

    if len(intersection) > 0:
        raise RequestValidationException(f"Validation error for composite object ID `{object_id}`, subobject IDs `{intersection}` are present both in `subobjects` and `deleted_subobjects`.")


class RequestValidationException(Exception):
    pass
