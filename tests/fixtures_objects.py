__all__ = ["test_link", "incorrect_object_values"]

test_link = {
    "object_id": 1,
    "object_type": "link",
    "object_name": "Google",
    "object_description": "Google's website",
    "object_data": {
        "link": "https://google.com"
    }
}

incorrect_object_values = [
    ("object_id", -1), ("object_id", "abc"),
    ("object_type", 1), ("object_type", "incorrect object type"),
    ("object_name", 123), ("object_name", ""), ("object_name", "a"*256),
    ("object_description", 1),
    ("object_data", None), ("object_data", ""), ("object_data", 1)
]

# incorrect_tag_values = [
#     ("tag_id", -1), ("tag_id", "abc"), 
#     ("tag_name", 123), ("tag_name", ""), ("tag_name", "a"*256),
#     ("tag_description", 1)
# ]