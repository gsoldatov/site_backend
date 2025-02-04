from datetime import datetime, timezone, timedelta


incorrect_tag_attributes = {
    "tag_id": [None, False, "str", [], {}, -1, 0],
    "tag_name": [None, False, [], {}, 1, "", "a" * 256],
    "tag_description": [None, False, [], {}, 1],
    "is_published": [None, [], {}, 1, "a"],
    "unallowed": ["unallowed"]
}


tag_list = [{
        "tag_id": x + 1,
        "created_at": datetime.now(tz=timezone.utc) + timedelta(minutes = x - 10 if x in (0, 4, 8) else x), # vowels first, consonants second
        "modified_at": datetime.now(tz=timezone.utc) + timedelta(minutes = x - 10 if x in (0, 4, 8) else x), # vowels first, consonants second
        "tag_name": chr(ord("a") + x) + str(x % 2),
        "tag_description": chr(ord("a") + x) + str(x % 2) + " description",
        "is_published": x % 2 == 0
    } for x in range(10)
]