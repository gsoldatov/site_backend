from datetime import datetime, timezone, timedelta


incorrect_tag_values = [
    ("tag_id", -1), ("tag_id", "abc"), 
    ("tag_name", 123), ("tag_name", ""), ("tag_name", "a"*256),
    ("tag_description", 1),
    ("is_published", 1), ("is_published", "abc")
]

tag_list = [{
        "tag_id": x + 1,
        "created_at": datetime.now(tz=timezone.utc) + timedelta(minutes = x - 10 if x in (0, 4, 8) else x), # vowels first, consonants second
        "modified_at": datetime.now(tz=timezone.utc) + timedelta(minutes = x - 10 if x in (0, 4, 8) else x), # vowels first, consonants second
        "tag_name": chr(ord("a") + x) + str(x % 2),
        "tag_description": chr(ord("a") + x) + str(x % 2) + " description",
        "is_published": x % 2 == 0
    } for x in range(10)
]