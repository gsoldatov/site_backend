from datetime import datetime, timedelta

from psycopg2.extensions import AsIs

from tests.fixtures.users import get_test_user, insert_users


__all__ = ["get_test_object", "get_test_object_data", "incorrect_object_values", "get_objects_attributes_list", 
            "links_data_list", "markdown_data_list", "to_do_lists_data_list", "composite_data_list",
            "add_composite_subobject", "add_composite_deleted_subobject", "get_composite_subobject_object_data",
            "insert_objects", "insert_links", "insert_markdown", "insert_to_do_lists", "insert_composite", "delete_objects"]


def get_test_object(object_id, object_type = None, created_at = None, modified_at = None, \
    object_name = None, object_description = None, is_published = None, owner_id = None, \
    pop_keys = [], composite_object_with_subobject_data = False):
    """
    Returns a dictionary representing an object, which can be sent in a request body or inserted into the database.
    Accepts `object_id` and, optionally, other object attributes (except for `object_data`, which is generated by the function).
    If `object_type` is omitted, its value is set based on `object_id`.
    If `owner_id` is omitted, it will not be returned in the response.

    Returnes dictionary contains `object_id`, `object_type`, `created_at`, `modified_at`, `object_name`, `object_description`,
    `is_published`, `owner_id` and `object_data` attributes.
    Attributes, which are not required, can be removed by adding them into `pop_keys` list.

    `object_data` is generated accordingly to `object_type` provided or set based on `object_id`.
    `composite_object_with_subobject_data` can be set to True to return a composite object with its first subobject containing object attributes & data.
    """
    if object_type is None:
        if 1 <= object_id <= 3:
            object_type = "link"
        elif 4 <= object_id <= 6:
            object_type = "markdown"
        elif 7 <= object_id <= 9:
            object_type = "to_do_list"
        elif 10 <= object_id <= 12:
            object_type = "composite"
        else:
            raise ValueError(f"Received an incorrect combination of object_id and object_type in get_test_object function: '{object_id}', '{object_type}'")
    
    curr_time = datetime.utcnow()
    created_at = created_at if created_at is not None else curr_time
    modified_at = modified_at if modified_at is not None else curr_time
    object_name = object_name if object_name is not None else f"Object #{object_id}"
    object_description = object_description if object_description is not None else f"Description to {object_name}"
    is_published = is_published if is_published is not None else False
    object_data = get_test_object_data(object_id, object_type, composite_object_with_subobject_data)["object_data"]

    obj = {"object_id": object_id, "object_type": object_type, "created_at": curr_time, "modified_at": curr_time, 
           "object_name": object_name, "object_description": object_description, "is_published": is_published, "object_data": object_data}
    if owner_id is not None:
        obj["owner_id"] = owner_id

    for k in pop_keys:
        obj.pop(k, None)
    return obj


def get_test_object_data(object_id, object_type = None, composite_object_with_subobject_data = False):
    """
    Returns a dict with data to insert into and object data table (links, markdown, etc.)
    If `object_type` is not provided, object type is chosen based on the `object_id` value.

    `composite_object_with_subobject_data` can be set to True to return a composite object with its first subobject containing object attributes & data.
    """
    if object_type is not None:
        func = _object_type_data_func_mapping.get(object_type)
        if func is None:
            raise ValueError(f"Received an incorrect object_type in get_test_object_data function: {object_type}")
        if object_type == "composite":
            return {"object_id": object_id, "object_data": func(object_id, composite_object_with_subobject_data)}
        else:
            return {"object_id": object_id, "object_data": func(object_id)}
    else:
        if 1 <= object_id <= 3:
            return {"object_id": object_id, "object_data": _get_link_object_data(object_id)}
        elif 4 <= object_id <= 6:
            return {"object_id": object_id, "object_data": _get_markdown_object_data(object_id)}
        elif 7 <= object_id <= 9:
            return {"object_id": object_id, "object_data": _get_to_do_list_object_data(object_id)}
        elif 10 <= object_id <= 12:
            return {"object_id": object_id, "object_data": _get_composite_object_data(object_id, composite_object_with_subobject_data)}
        else:
            raise ValueError(f"Received an incorrect object id in get_test_object_data function: {object_id}")


# Data generating functions
def _get_link_object_data(id):
    return {"link": f"https://test.link.{id}"}

def _get_markdown_object_data(id):
    return {"raw_text": f"Raw markdown text #{id}"}

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
        } for x in range(max(id % 20, 1))]
    }

def _get_composite_object_data(id, composite_object_with_subobject_data = False):
    so = {"object_id": 1, "row": 0, "column": 0, "selected_tab": 0, "is_expanded": True}
    if composite_object_with_subobject_data:
        so["object_name"] = "subobject name"
        so["object_description"] = "subobject description"
        so["is_published"] = False
        so["object_type"] = "link"
        so["object_data"] = get_composite_subobject_object_data(1)

    return { "subobjects": [so], "deleted_subobjects": []}

_object_type_data_func_mapping = {"link": _get_link_object_data, "markdown": _get_markdown_object_data, "to_do_list": _get_to_do_list_object_data, "composite": _get_composite_object_data}

def _get_obj_type(x):
    return "link" if 1 <= x <= 10 else "markdown" if 11 <= x <= 20 else "to_do_list" if 21 <= x <= 30 else "composite" if 31 <= x <= 40 else "unknown"


def _get_obj_timestamp(x):
    """
    IDs dividable by 4 are created/modified earlier than IDs which are not.
    IDs dividable by 4 are sorted in descending order by timestamp; IDs not dividable by 4 are sorted in ascending order.
    E.g.: 
    ... 16 12 8 4 1 2 3 5 6 7 9 ...
    """
    return datetime.utcnow() + timedelta(minutes = -x if x % 4 == 0 else x)


def get_objects_attributes_list(min_id, max_id, owner_id = 1):
    """
    Returns a list object attributes for each object_id between `min_id` and `max_id` including.
    If `owner_id` is passed, it will be used as `owner_id` of each object (default value is 1).
    id <= 10 => link
    id <= 20 => markdown
    id <= 30 => to-do list
    id <= 40 => composite
    """
    return [{
        "object_id": x,
        "object_type": f"{_get_obj_type(x)}",
        "created_at": _get_obj_timestamp(x),
        "modified_at": _get_obj_timestamp(x),
        "object_name": chr(ord("a") + x - 1) + str((x+1) % 2),
        "object_description": chr(ord("a") + x - 1) + str((x+1) % 2) + " description",
        "is_published": False,
        "owner_id": owner_id
    } for x in range(min_id, max_id + 1)]


# Composite subobject modification
def add_composite_subobject(composite, object_id, row = None, column = None, selected_tab = 0, is_expanded = True, \
    object_name = None, object_description = None, object_type = None, is_published = None, owner_id = None, \
    addedTags = None, removed_tag_ids = None, object_data = None):
    """
    Accepts a `composite` (dict respesenting `object_data` property of a composite object)
    and inserts a new subobject with provided or default props and data updates (if specified).
    """
    # Check if subobject attributes/data are correctly provided
    for attr in (object_name, object_description, object_type, is_published, owner_id, addedTags, removed_tag_ids, object_data):
        if attr is not None:
            if None in (object_name, object_description, object_type, is_published, object_data):
                raise Exception("Received incorrect subobject attributes or data when adding a new subobject.")
            break
    
    # Set default column value (last existing column)
    if column is None:
        column = 0
        for so in composite["object_data"]["subobjects"]:
            if so["column"] > column:
                column = so["column"]
    
    # Set default row value (new row)
    if row is None:
        row = 0
        for so in composite["object_data"]["subobjects"]:
            if so["row"] >= row and so["column"] == column:
                row = so["row"] + 1

    # Add new subobject
    new_so = {"object_id": object_id, "row": row, "column": column, "selected_tab": selected_tab, "is_expanded": is_expanded}
    if object_name != None:
        new_so["object_name"] = object_name
        new_so["object_description"] = object_description
        new_so["object_type"] = object_type
        new_so["is_published"] = is_published
        if owner_id is not None:
            new_so["owner_id"] = owner_id
        new_so["object_data"] = object_data

    composite["object_data"]["subobjects"].append(new_so)


def add_composite_deleted_subobject(composite, object_id, is_full_delete = True):
    """
    Accepts a `composite` (dict respesenting `object_data` property of a composite object)
    and inserts a new deleted subobject.
    """
    composite["object_data"]["deleted_subobjects"].append({"object_id": object_id, "is_full_delete": is_full_delete})


def get_composite_subobject_object_data(object_id):
    """
    Returns a dict with object data to be used as composite subobject data.
    """
    return get_test_object_data(object_id)["object_data"]


# Fixed value and object data lists to be supplied into insert functions below
incorrect_object_values = [
    ("object_id", -1), ("object_id", "abc"),
    ("object_type", 1), ("object_type", "incorrect object type"),
    ("object_name", 123), ("object_name", ""), ("object_name", "a"*256),
    ("object_description", 1),
    ("is_published", 1), ("is_published", "str"), ("is_published", None),
    ("owner_id", -1), ("owner_id", "str"), ("owner_id", True),
    ("object_data", None), ("object_data", ""), ("object_data", 1)
]

links_data_list = [{
        "object_id": x,
        "object_data": _get_link_object_data(x)
    } for x in range(1, 11)
]

markdown_data_list = [{
        "object_id": x,
        "object_data": _get_markdown_object_data(x)
    } for x in range(11, 21)
]

to_do_lists_data_list = [{
        "object_id": x,
        "object_data": _get_to_do_list_object_data(x)
    } for x in range(21, 31)
]

composite_data_list = [{
        "object_id": x,
        "object_data": _get_composite_object_data(x)
    } for x in range(31, 41)
]


# Insert/delete functions for manipulating test data in the database
def insert_objects(objects, db_cursor):
    """
    Inserts a list of objects into objects table.
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s, %s, %s)" for _ in range(len(objects))))
    table = "objects"
    params = [AsIs(table)]
    for o in objects:
        params.extend(o.values())
    db_cursor.execute(query, params)


def insert_links(links, db_cursor):
    """
    Inserts link objects' data into the database.
    `links` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {"link": ...}}
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(links))))
    table = "links"
    params = [AsIs(table)]
    for l in links:
        params.append(l["object_id"])
        params.append(l["object_data"]["link"])
    db_cursor.execute(query, params)


def insert_markdown(markdown, db_cursor):
    """
    Inserts markdown objects' data into the database.
    `markdown` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {"raw_text": ...}}
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(markdown))))
    table = "markdown"
    params = [AsIs(table)]
    for m in markdown:
        params.append(m["object_id"])
        params.append(m["object_data"]["raw_text"])
    db_cursor.execute(query, params)


def insert_to_do_lists(lists, db_cursor):
    """
    Inserts to-do list objects' data into the database.
    `lists` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {...}}
    """
    # to_do_lists
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(lists))))
    table = "to_do_lists"
    params = [AsIs(table)]
    for l in lists:
        params.extend([l["object_id"], l["object_data"]["sort_type"]])
    db_cursor.execute(query, params)

    # to_do_list_items
    num_of_lines = sum((len(t["object_data"]["items"]) for t in lists))
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s, %s)" for _ in range(num_of_lines)))
    table = "to_do_list_items"
    params = [AsIs(table)]
    for l in lists:
        for i in l["object_data"]["items"]:
            params.append(l["object_id"])
            params.extend(i.values())
    db_cursor.execute(query, params)


def insert_composite(composite, db_cursor):
    """
    Inserts composite objects' data into the database.
    `composite` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {...}}
    """
    num_of_lines = sum((len(c["object_data"]["subobjects"]) for c in composite))
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s)" for _ in range(num_of_lines)))
    table = "composite"
    params = [AsIs(table)]
    for c in composite:
        for so in c["object_data"]["subobjects"]:
            params.append(c["object_id"])
            params.extend(so.values())
    db_cursor.execute(query, params)


def delete_objects(object_ids, db_cursor):
    """
    Deletes objects with provided IDs (this should also result in a cascade delete of related data from other tables).
    """
    table = "objects"
    query = "DELETE FROM %s WHERE object_id IN (" + ", ".join(("%s" for _ in range(len(object_ids)))) + ")"
    params = [AsIs(table)]
    params.extend(object_ids)
    db_cursor.execute(query, params)


# Sets of mock data insertions in the database
def insert_data_for_view_objects_as_anonymous(object_ids, db_cursor, object_type = "link"):
    """
    Inserts another user and a set of likn objects in the database.
    Objects belong to different users and are partially published.
    If `object_type` is provided, inserted objects have it as their object type (defaults to "link").
    """
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user
    object_attributes = [get_test_object(i, object_type=object_type, owner_id=1, pop_keys=["object_data"]) for i in range(1, 11)]
    # object_attributes = get_objects_attributes_list(1, 10)
    for i in range(5, 10):
        object_attributes[i]["owner_id"] = 2
    for i in range(1, 10, 2):
        object_attributes[i]["is_published"] = True
    insert_objects(object_attributes, db_cursor)
    data_insert_func = insert_links if object_type == "link" else insert_markdown if object_type == "markdown" else \
        insert_to_do_lists if object_type == "to_do_list" else insert_composite
    data_insert_func([get_test_object_data(i, object_type=object_type) for i in range(1, 11)], db_cursor)