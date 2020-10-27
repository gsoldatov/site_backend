from datetime import datetime, timedelta


__all__ = ["test_link", "test_link2", "test_link3", "incorrect_object_values", "object_list", "links_list"]

test_link = {
    "object_id": 1,
    "object_type": "link",
    "object_name": "Google",
    "object_description": "Google's website",
    "object_data": {
        "link": "https://google.com"
    }
}

test_link2 = {
    "object_id": 2,
    "object_type": "link",
    "object_name": "Wikipedia",
    "object_description": "",
    "object_data": {
        "link": "https://wikipedia.org"
    }
}

test_link3 = {
    "object_id": 3,
    "object_type": "link",
    "object_name": "BBC",
    "object_description": "BBC website",
    "object_data": {
        "link": "https://bbc.co.uk"
    }
}

incorrect_object_values = [
    ("object_id", -1), ("object_id", "abc"),
    ("object_type", 1), ("object_type", "incorrect object type"),
    ("object_name", 123), ("object_name", ""), ("object_name", "a"*256),
    ("object_description", 1),
    ("object_data", None), ("object_data", ""), ("object_data", 1)
]

def _get_obj_type(x):
    return "link" if 1 <= x <= 10 else "unknown"

def _get_obj_timestamp(x):
    """
    IDs dividable by 4 are created/modified earlier than IDs which are not.
    IDs dividable by 4 are sorted in descending order by timestamp; IDs not dividable by 4 are sorted in ascending order.
    E.g.: 
    ... 16 12 8 4 1 2 3 5 6 7 9 ...
    """
    return datetime.utcnow() + timedelta(minutes = -x if x % 4 == 0 else x)


object_list = [{
        "object_id": x,
        "object_type": f"{_get_obj_type(x)}",
        "created_at": _get_obj_timestamp(x),
        "modified_at": _get_obj_timestamp(x),
        "object_name": chr(ord("a") + x) + str((x+1) % 2),
        "object_description": chr(ord("a") + x) + str((x+1) % 2) + " description"
    } for x in range(1, 11)
]

links_list = [{
        "object_id": x,
        "link": f"https://website{x}.com"
    } for x in range(1, 11)
]
