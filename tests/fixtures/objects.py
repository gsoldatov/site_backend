from datetime import datetime, timedelta

from psycopg2.extensions import AsIs


__all__ = ["get_test_object", "get_test_object_data", "incorrect_object_values", "get_object_list", "links_list", "markdown_list",
            "insert_objects", "insert_links", "insert_markdown", "delete_objects"]


def get_test_object(id, name = None, pop_keys = []):
    """
    Returns a new dictionary for objects table with attributes specified in pop_keys popped from it.
    If name is not provided, uses one of the default values (which are bound to specific IDs).
    """
    if 1 <= id <= 3:
        object_type = "link"
        object_data = {"link": _links[id]}
    elif 4 <= id <= 6:
        object_type = "markdown"
        object_data = {"raw_text": _markdown_raw_text[id]}
    elif name is not None:
        object_type = "link"
        object_data = {"link": f"https://test.link.{id}"}        
    else:
        raise ValueError(f"Received an incorrect object id in get_test_object function: {id}")
    
    name = name or _object_names[id]
    curr_time = datetime.utcnow()

    obj = {"object_id": id, "object_type": object_type, "created_at": curr_time, "modified_at": curr_time, "object_name": name, "object_description": f"Everything Related to {name}",
        "object_data": object_data}
    for k in pop_keys:
        obj.pop(k, None)
    return obj


def get_test_object_data(i):
    """
    Returns a dict with data to insert into and object data table (links, markdown, etc.)
    """
    if 1 <= i <= 3:
        return {"object_id": i, "link": _links[i]}
    elif 4 <= i <= 6:
        return {"object_id": i, "raw_text": _markdown_raw_text[i]}
    else:
        raise ValueError(f"Received an incorrect object id in get_test_object_data function: {i}")

_object_names = {1: "Google", 2: "Wikipedia", 3: "BBC", 4: "Text #4", 5: "Text #5", 6: "Text #6"}
_links = {1: "https://google.com", 2: "https://wikipedia.org", 3: "https://bbc.co.uk"}
_markdown_raw_text = {4: "Raw markdown text #4", 5: "Raw markdown text #5", 6: "Raw markdown text #6"}


incorrect_object_values = [
    ("object_id", -1), ("object_id", "abc"),
    ("object_type", 1), ("object_type", "incorrect object type"),
    ("object_name", 123), ("object_name", ""), ("object_name", "a"*256),
    ("object_description", 1),
    ("object_data", None), ("object_data", ""), ("object_data", 1)
]


def _get_obj_type(x):
    return "link" if 1 <= x <= 10 else "markdown" if 11 <= x <= 20 else "unknown"


def _get_obj_timestamp(x):
    """
    IDs dividable by 4 are created/modified earlier than IDs which are not.
    IDs dividable by 4 are sorted in descending order by timestamp; IDs not dividable by 4 are sorted in ascending order.
    E.g.: 
    ... 16 12 8 4 1 2 3 5 6 7 9 ...
    """
    return datetime.utcnow() + timedelta(minutes = -x if x % 4 == 0 else x)


def get_object_list(min_id, max_id):
    """
        Returns a list object attributes for each object_id between min_id and max_id including.
        id <= 10 => link
        id <= 20 => markdown
    """
    return [{
        "object_id": x,
        "object_type": f"{_get_obj_type(x)}",
        "created_at": _get_obj_timestamp(x),
        "modified_at": _get_obj_timestamp(x),
        "object_name": chr(ord("a") + x - 1) + str((x+1) % 2),
        "object_description": chr(ord("a") + x - 1) + str((x+1) % 2) + " description"
    } for x in range(min_id, max_id + 1)]


links_list = [{
        "object_id": x,
        "link": f"https://website{x}.com"
    } for x in range(1, 11)
]


markdown_list = [{
        "object_id": x,
        "raw_text": f"Raw markdown text #{x}"
    } for x in range(11, 21)
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


def insert_markdown(texts, db_cursor, config):
    """
    Inserts a list of markdown texts into <db_schema>.markdown table.
    """
    cursor = db_cursor(apply_migrations = True)
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(texts))))
    table = config["db"]["db_schema"] + ".markdown"
    params = [AsIs(table)]
    for l in texts:
        params.extend(l.values())
    cursor.execute(query, params)


def delete_objects(object_ids, db_cursor, config):
    """
    Deletes objects with provided IDs (this should also result in a cascade delete of related data from other tables).
    """
    cursor = db_cursor(apply_migrations = True)
    table = config["db"]["db_schema"] + ".objects"
    query = "DELETE FROM %s WHERE object_id IN (" + ", ".join(("%s" for _ in range(len(object_ids)))) + ")"
    params = [AsIs(table)]
    params.extend(object_ids)
    cursor.execute(query, params)
