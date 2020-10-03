from datetime import datetime #, timedelta

__all__ = ["test_link", "incorrect_object_values", "objects_list", "urls_list"]

test_link = {
    "object_id": 1,
    "object_type": "link",
    "object_name": "Google",
    "object_description": "Google's website",
    "object_data": {
        "link": "https://google.com"
    }
}

# test_link2 = {
#     "object_id": 2,
#     "object_type": "link",
#     "object_name": "Wikipedia",
#     "object_description": "",
#     "object_data": {
#         "link": "https://wikipedia.org"
#     }
# }

incorrect_object_values = [
    ("object_id", -1), ("object_id", "abc"),
    ("object_type", 1), ("object_type", "incorrect object type"),
    ("object_name", 123), ("object_name", ""), ("object_name", "a"*256),
    ("object_description", 1),
    ("object_data", None), ("object_data", ""), ("object_data", 1)
]

def _get_obj_type(x):
    return "link" #TODO insert other object types when they will be required for tests

objects_list = [{
        "object_id": x,
        "object_type": f"{_get_obj_type(x)}",
        "created_at": datetime.utcnow(), #TODO add sorting rules
        "modified_at": datetime.utcnow(), #TODO add sorting rules
        "object_name": f"{_get_obj_type(x)} {x}",
        "object_description": f"{_get_obj_type(x)} {x} description"
    } for x in range(1, 11)
]

urls_list = [{
        "object_id": x,
        "link": f"https://website{x}.com"
    } for x in range(1, 11)
]
