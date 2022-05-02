from datetime import datetime, timedelta

from psycopg2.extensions import AsIs


__all__ = ["get_test_tag", "incorrect_tag_values", "tag_list", "insert_tags", "delete_tags"]

def get_test_tag(i, tag_name = None, tag_description = None, created_at = None, modified_at = None, pop_keys = []):
    """
    Returns a new dictionary for tags table with attributes specified in pop_keys popped from it.
    If name is not provided, uses one of the default values (which are bound to specific IDs).
    """
    tag_name = tag_name if tag_name is not None else _tag_names.get(i, f"tag name {i}")
    tag_description = tag_description if tag_description is not None else f"Everything Related to {tag_name}"

    curr_time = datetime.utcnow()
    created_at = created_at if created_at is not None else curr_time
    modified_at = modified_at if modified_at is not None else curr_time   

    
    curr_time = datetime.utcnow()
    tag = {"tag_id": i, "created_at": created_at, "modified_at": modified_at, "tag_name": tag_name, "tag_description": tag_description}
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

def insert_tags(tags, db_cursor, generate_tag_ids = False):
    """
    Inserts a list of tags into tags table.
    """  
    table = "tags"
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
    db_cursor.execute(query, params)


def delete_tags(tag_ids, db_cursor):
    """
    Deletes tags with provided IDs (this should also result in a cascade delete of related data from other tables).
    """
    table = "tags"
    query = "DELETE FROM %s WHERE tag_id IN (" + ", ".join(("%s" for _ in range(len(tag_ids)))) + ")"
    params = [AsIs(table)]
    params.extend(tag_ids)
    db_cursor.execute(query, params)
