from datetime import datetime, timedelta

__all__ = ["test_tag", "test_tag2", "test_tag3", "incorrect_tag_values", "tag_list"]

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

test_tag3 = {
    "tag_id": 3,
    "tag_name": "books",
    "tag_description": "Everything related to books"
}

incorrect_tag_values = [
    ("tag_id", -1), ("tag_id", "abc"), 
    ("tag_name", 123), ("tag_name", ""), ("tag_name", "a"*256),
    ("tag_description", 1)
]

tag_list = [{
        "tag_id": x + 1,
        "created_at": datetime.utcnow() + timedelta(minutes = x - 10 if x in (0, 4, 8) else x), # vowels first, consonants second
        "modified_at": datetime.utcnow() + timedelta(minutes = x - 10 if x in (0, 4, 8) else x), # vowels first, consonants second
        "tag_name": chr(ord("a") + x),
        "tag_description": chr(ord("a") + x) + " description"
    } for x in range(10)
]