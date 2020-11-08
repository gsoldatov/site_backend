from datetime import datetime, timedelta

from psycopg2.extensions import AsIs


__all__ = ["get_test_tag", "incorrect_tag_values", "tag_list", "insert_tags"]

def get_test_tag(i, pop_keys = []):
    """
    Returns a new tag dictionary with attributes specified in pop_keys popped from it.
    """
    name = _tag_names[i]
    curr_time = datetime.utcnow()
    tag = {"tag_id": i, "created_at": curr_time, "modified_at": curr_time, "tag_name": name, "tag_description": f"Everything Related to {name}"}
    for k in pop_keys:
        tag.pop(k, None)
    return tag

_tag_names = {1: "Music", 2: "Movies", 3: "Books"}

incorrect_tag_values = [
    ("tag_id", -1), ("tag_id", "abc"), 
    ("tag_name", 123), ("tag_name", ""), ("tag_name", "a"*256),
    ("tag_description", 1)
]

tag_list = [{
        "tag_id": x + 1,
        "created_at": datetime.utcnow() + timedelta(minutes = x - 10 if x in (0, 4, 8) else x), # vowels first, consonants second
        "modified_at": datetime.utcnow() + timedelta(minutes = x - 10 if x in (0, 4, 8) else x), # vowels first, consonants second
        "tag_name": chr(ord("a") + x) + str(x % 2),
        "tag_description": chr(ord("a") + x) + str(x % 2) + " description"
    } for x in range(10)
]

def insert_tags(tags, db_cursor, config, generate_tag_ids = False):
    """
    Inserts a list of tags into <db_schema>.tags table.
    """
    cursor = db_cursor(apply_migrations = True)    
    table = config["db"]["db_schema"] + ".tags"
    params = [AsIs(table)]
    query = ""

    if generate_tag_ids:
        query = "INSERT INTO %s VALUES " + ", ".join(("(DEFAULT, %s, %s, %s, %s)" for _ in range(len(tags))))
        for t in tags:
            params.extend((t[k] for k in t if k != "tag_id"))
    else:
        query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s)" for _ in range(len(tags))))
        for t in tags:
            params.extend(t.values())
    cursor.execute(query, params)
