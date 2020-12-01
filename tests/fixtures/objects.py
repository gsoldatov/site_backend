from datetime import datetime, timedelta

from psycopg2.extensions import AsIs


__all__ = ["get_test_object_link", "get_test_link", "incorrect_object_values", "object_list", "links_list", 
            "insert_objects", "insert_links"]

def get_test_object_link(i, pop_keys = []):
    """
    Returns a new link dictionary for objects table with attributes specified in pop_keys popped from it.
    """
    name = _object_names[i]
    curr_time = datetime.utcnow()
    link = {"object_id": i, "object_type": "link", "created_at": curr_time, "modified_at": curr_time, "object_name": name, "object_description": f"Everything Related to {name}",
        "object_data": {"link": _links[i]}}
    for k in pop_keys:
        link.pop(k, None)
    return link


def get_test_link(i):
    """
    Returns a new link dictionary for links table.
    """
    return {"object_id": i, "link": _links[i]}

_object_names = {1: "Google", 2: "Wikipedia", 3: "BBC"}
_links = {1: "https://google.com", 2: "https://wikipedia.org", 3: "https://bbc.co.uk"}

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
        "object_name": chr(ord("a") + x - 1) + str((x+1) % 2),
        "object_description": chr(ord("a") + x - 1) + str((x+1) % 2) + " description"
    } for x in range(1, 11)
]


links_list = [{
        "object_id": x,
        "link": f"https://website{x}.com"
    } for x in range(1, 11)
]


def insert_objects(objects, db_cursor, config):
    """
    Inserts a list of objects into <db_schema>.objects table.
    """
    cursor = db_cursor(apply_migrations = True)
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s)" for _ in range(len(objects))))
    table = config["db"]["db_schema"] + ".objects"
    params = [AsIs(table)]
    for o in objects:
        params.extend(o.values())
    cursor.execute(query, params)


def insert_links(links, db_cursor, config):
    """
    Inserts a list of links into <db_schema>.links table.
    """
    cursor = db_cursor(apply_migrations = True)
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(links))))
    table = config["db"]["db_schema"] + ".links"
    params = [AsIs(table)]
    for l in links:
        params.extend(l.values())
    cursor.execute(query, params)