from datetime import datetime, timedelta

from psycopg2.extensions import AsIs


__all__ = ["get_test_object", "get_test_object_data", "incorrect_object_values", "get_object_list", "links_list", "markdown_list", "to_do_lists_list",
            "insert_objects", "insert_links", "insert_markdown", "insert_to_do_lists", "delete_objects"]


def get_test_object(id, name = None, pop_keys = []):
    """
    Returns a new dictionary for objects table with attributes specified in pop_keys popped from it.
    If name is not provided, uses one of the default values (which are bound to specific IDs).
    """
    if 1 <= id <= 3:
        object_type = "link"
        object_data = {"link": _get_link(id)}
    elif 4 <= id <= 6:
        object_type = "markdown"
        object_data = {"raw_text": _get_markdown_raw_text(id)}
    elif 7 <= id <= 9:
        object_type = "to_do_list"
        object_data = _get_to_do_list_object_data(id)
    elif name is not None:
        object_type = "link"
        object_data = {"link": _get_link(id)}
    else:
        raise ValueError(f"Received an incorrect combination of object id and name in get_test_object function: '{id}', '{name}'")
    
    name = name or _get_object_name(id)
    curr_time = datetime.utcnow()

    obj = {"object_id": id, "object_type": object_type, "created_at": curr_time, "modified_at": curr_time, "object_name": name, "object_description": f"Everything Related to {name}",
        "object_data": object_data}
    for k in pop_keys:
        obj.pop(k, None)
    return obj


# Used in object type specific tests
def get_test_object_data(id):
    """
    Returns a dict with data to insert into and object data table (links, markdown, etc.)
    """
    if 1 <= id <= 3:
        return {"object_id": id, "link": _get_link(id)}
    elif 4 <= id <= 6:
        return {"object_id": id, "raw_text": _get_markdown_raw_text(id)}
    elif 7 <= id <= 9:
        return {"object_id": id, "object_data": _get_to_do_list_object_data(id)}
    else:
        raise ValueError(f"Received an incorrect object id in get_test_object_data function: {id}")


_get_object_name = lambda id: f"Object #{id}"
_get_link = lambda id: f"https://test.link.{id}"
_get_markdown_raw_text = lambda id: f"Raw markdown text #{id}"
def _get_to_do_list_object_data(id):
    _item_states = ["active", "completed", "optional", "cancelled"]
    return {
        "sort_type": "default",
        "items": [{     # item key order must match the order in which columns are declared in DB schemas, because to-do lists tests depend on this order when comparing added/updated data
            "item_number": x + 1,
            "item_state": _item_states[x % 4],
            "item_text": f"To-do list #{id}, item #{x+1}",
            "commentary": f"Commentary for to-do list #{id}, item #{x+1}",
            "indent": 0 if x % 4 < 2 else 1,
            "is_expanded": True
        } for x in range(id)]
    }


incorrect_object_values = [
    ("object_id", -1), ("object_id", "abc"),
    ("object_type", 1), ("object_type", "incorrect object type"),
    ("object_name", 123), ("object_name", ""), ("object_name", "a"*256),
    ("object_description", 1),
    ("object_data", None), ("object_data", ""), ("object_data", 1)
]


def _get_obj_type(x):
    return "link" if 1 <= x <= 10 else "markdown" if 11 <= x <= 20 else "to_do_list" if 21 <= x <= 30 else "unknown"


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
        id <= 30 => to-do list
    """
    return [{
        "object_id": x,
        "object_type": f"{_get_obj_type(x)}",
        "created_at": _get_obj_timestamp(x),
        "modified_at": _get_obj_timestamp(x),
        "object_name": chr(ord("a") + x - 1) + str((x+1) % 2),
        "object_description": chr(ord("a") + x - 1) + str((x+1) % 2) + " description"
    } for x in range(min_id, max_id + 1)]


# Object data lists to be supplied into insert functions below
links_list = [{
        "object_id": x,
        "link": _get_link(x)
    } for x in range(1, 11)
]


markdown_list = [{
        "object_id": x,
        "raw_text": _get_markdown_raw_text(x)
    } for x in range(11, 21)
]


to_do_lists_list = [{
        "object_id": x,
        "object_data": _get_to_do_list_object_data(x)
    } for x in range(21, 31)
]


# Insert/delete functions for manipulating test data in the database
def insert_objects(objects, db_cursor, config):
    """
    Inserts a list of objects into <db_schema>.objects table.
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s)" for _ in range(len(objects))))
    table = config["db"]["db_schema"] + ".objects"
    params = [AsIs(table)]
    for o in objects:
        params.extend(o.values())
    db_cursor.execute(query, params)


def insert_links(links, db_cursor, config):
    """
    Inserts a list of links into <db_schema>.links table.
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(links))))
    table = config["db"]["db_schema"] + ".links"
    params = [AsIs(table)]
    for l in links:
        params.extend(l.values())
    db_cursor.execute(query, params)


def insert_markdown(texts, db_cursor, config):
    """
    Inserts a list of markdown texts into <db_schema>.markdown table.
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(texts))))
    table = config["db"]["db_schema"] + ".markdown"
    params = [AsIs(table)]
    for l in texts:
        params.extend(l.values())
    db_cursor.execute(query, params)


def insert_to_do_lists(lists, db_cursor, config):
    # to_do_lists
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(lists))))
    table = config["db"]["db_schema"] + ".to_do_lists"
    params = [AsIs(table)]
    for l in lists:
        params.extend([l["object_id"], l["object_data"]["sort_type"]])
    db_cursor.execute(query, params)

    # to_do_list_items
    num_of_lines = sum((len(t["object_data"]["items"]) for t in lists))
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s, %s)" for _ in range(num_of_lines)))
    table = config["db"]["db_schema"] + ".to_do_list_items"
    params = [AsIs(table)]
    for l in lists:
        for i in l["object_data"]["items"]:
            params.append(l["object_id"])
            params.extend(i.values())
    db_cursor.execute(query, params)


def delete_objects(object_ids, db_cursor, config):
    """
    Deletes objects with provided IDs (this should also result in a cascade delete of related data from other tables).
    """
    table = config["db"]["db_schema"] + ".objects"
    query = "DELETE FROM %s WHERE object_id IN (" + ", ".join(("%s" for _ in range(len(object_ids)))) + ")"
    params = [AsIs(table)]
    params.extend(object_ids)
    db_cursor.execute(query, params)
