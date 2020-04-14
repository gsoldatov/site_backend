__all__ = ["test_tag", "test_tag2", "incorrect_tag_values"]

test_tag = {
    "tag_id": 1,
    "tag_name": "music",
    "tag_description": "Everything related to music"
}

test_tag2 = {
    "tag_id": 2,
    "tag_name": "movies",
    "tag_description": "Everything related to movies"
}

incorrect_tag_values = [
    ("tag_id", -1), ("tag_id", "abc"), 
    ("tag_name", 123), ("tag_name", ""), ("tag_name", "a"*256),
    ("tag_description", 1)
]