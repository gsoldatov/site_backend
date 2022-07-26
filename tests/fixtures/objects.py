from datetime import datetime, timedelta

from psycopg2.extensions import AsIs

from tests.util import parse_iso_timestamp
from tests.fixtures.users import get_test_user, insert_users
from tests.fixtures.objects_tags import insert_objects_tags
from tests.fixtures.tags import get_test_tag, insert_tags


__all__ = ["get_test_object", "get_test_object_data", "incorrect_object_values", "get_objects_attributes_list", 
            "links_data_list", "markdown_data_list", "to_do_lists_data_list", "composite_data_list",
            "add_composite_subobject", "add_composite_deleted_subobject", "get_composite_subobject_object_data",
            "insert_objects", "insert_links", "insert_markdown", "insert_to_do_lists", "insert_composite", "insert_composite_properties", "delete_objects"]


def get_test_object(object_id, object_type = None, created_at = None, modified_at = None, \
    object_name = None, object_description = None, is_published = None, display_in_feed = None, feed_timestamp = None, \
    show_description = None, owner_id = None, \
    pop_keys = [], composite_subobject_object_type = None):
    """
    Returns a dictionary representing an object, which can be sent in a request body or inserted into the database.
    Accepts `object_id` and, optionally, other object attributes (except for `object_data`, which is generated by the function).
    If `object_type` is omitted, its value is set based on `object_id`.
    If `owner_id` is omitted, it will not be returned in the response.

    Returnes dictionary contains `object_id`, `object_type`, `created_at`, `modified_at`, `object_name`, `object_description`,
    `is_published`, `display_in_feed`, `feed_timestamp`, `show_description`, `owner_id` and `object_data` attributes.
    Attributes, which are not required, can be removed by adding them into `pop_keys` list.

    `object_data` is generated accordingly to `object_type` provided or set based on `object_id`.
    If `composite_subobject_object_type` is set, composite object is returned with its first subobject containing object attributes & data of the specified type.
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
    display_in_feed = display_in_feed if display_in_feed is not None else False
    feed_timestamp = feed_timestamp if feed_timestamp is not None else curr_time.isoformat() + "Z"
    show_description = show_description if show_description is not None else False
    object_data = get_test_object_data(object_id, object_type, composite_subobject_object_type)["object_data"]

    obj = {"object_id": object_id, "object_type": object_type, "created_at": curr_time, "modified_at": curr_time, 
           "object_name": object_name, "object_description": object_description, "is_published": is_published, 
           "display_in_feed": display_in_feed, "feed_timestamp": feed_timestamp, "show_description": show_description,
           "object_data": object_data}
    if owner_id is not None:
        obj["owner_id"] = owner_id

    for k in pop_keys:
        obj.pop(k, None)
    return obj


def get_test_object_data(object_id, object_type = None, composite_subobject_object_type = None):
    """
    Returns a dict with data to insert into and object data table (links, markdown, etc.)
    If `object_type` is not provided, object type is chosen based on the `object_id` value.

    If `composite_subobject_object_type` is set, composite object is returned with its first subobject containing object attributes & data of the specified type.
    """
    if object_type is not None:
        func = _object_type_data_func_mapping.get(object_type)
        if func is None:
            raise ValueError(f"Received an incorrect object_type in get_test_object_data function: {object_type}")
        if object_type == "composite":
            return {"object_id": object_id, "object_data": func(object_id, composite_subobject_object_type)}
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
            return {"object_id": object_id, "object_data": _get_composite_object_data(object_id, composite_subobject_object_type)}
        else:
            raise ValueError(f"Received an incorrect object id in get_test_object_data function: {object_id}")


# Data generating functions
def _get_link_object_data(id):
    return {"link": f"https://test.link.{id}", "show_description_as_link": False}

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

def _get_composite_object_data(id, composite_subobject_object_type = None):
    so = {"object_id": 1, "row": 0, "column": 0, "selected_tab": 0, "is_expanded": True, "show_description_composite": "inherit", "show_description_as_link_composite": "inherit"}
    if composite_subobject_object_type:
        so["object_name"] = "subobject name"
        so["object_description"] = "subobject description"
        so["is_published"] = False
        so["display_in_feed"] = False
        so["feed_timestamp"] = datetime.utcnow().isoformat() + "Z"
        so["show_description"] = False
        so["object_type"] = composite_subobject_object_type
        so["object_data"] = get_composite_subobject_object_data(1, object_type=composite_subobject_object_type)

    return { "subobjects": [so], "deleted_subobjects": [], "display_mode": "basic", "numerate_chapters": False }

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
    delta = -x if x % 4 == 0 else x
    return datetime.utcnow() + timedelta(minutes=delta)


def _get_object_feed_timestamp(x):
    """
    Returns string feed timestamp based on the provided object ID `x`.
    If x % 4 == 0, returns empty string.
    If x % 4 == 1, returns current time + 10 * x days.
    If x % 4 == 2, returns empty string.
    If x % 4 == 1, returns current time - 10 * x days.
    """
    if x % 2 == 0: return ""
    delta = 10 * x * (1 if x % 4 == 1 else -1)
    return (datetime.utcnow() + timedelta(days=delta)).isoformat() + "Z"


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
        "display_in_feed": False,
        "feed_timestamp": _get_object_feed_timestamp(x),
        "show_description": False,
        "owner_id": owner_id
    } for x in range(min_id, max_id + 1)]


# Composite subobject modification
def add_composite_subobject(composite, object_id, row = None, column = None, selected_tab = 0, is_expanded = True, \
    show_description_composite = "inherit", show_description_as_link_composite = "inherit", \
    object_name = None, object_description = None, object_type = None, is_published = None, 
    display_in_feed = None, feed_timestamp = None, show_description = None, owner_id = None, \
    object_data = None):
    """
    Accepts a `composite` (dict respesenting `object_data` property of a composite object)
    and inserts a new subobject with provided or default props and data updates (if specified).
    """
    # Check if subobject attributes/data are correctly provided
    locals_ = locals()
    subobject_object_attributes = ("object_name", "object_description", "object_type", "is_published", "display_in_feed", "feed_timestamp", 
        "show_description", "owner_id", "object_data")
    subobject_object_attribute_values = {attr: locals_.get(attr) for attr in subobject_object_attributes}
    required_subobject_object_attribute_values = {attr: locals_.get(attr) for attr in ("object_name", "object_type")}
    optional_subobject_object_attributes = ("owner_id",)

    for attr in subobject_object_attributes:
        if subobject_object_attribute_values[attr] is not None:
            if None in required_subobject_object_attribute_values:
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
    new_so = {"object_id": object_id, "row": row, "column": column, "selected_tab": selected_tab, "is_expanded": is_expanded,
                "show_description_composite": show_description_composite, "show_description_as_link_composite": show_description_as_link_composite}
    if object_name != None:
        default_values = get_test_object(object_id, object_type=object_type, object_name=object_name)
        for attr in subobject_object_attributes:
            if attr in optional_subobject_object_attributes:
                if subobject_object_attribute_values[attr] is not None:
                    new_so[attr] = subobject_object_attribute_values[attr]
            else:
                new_so[attr] = subobject_object_attribute_values[attr] if subobject_object_attribute_values[attr] is not None else default_values[attr]

    composite["object_data"]["subobjects"].append(new_so)


def add_composite_deleted_subobject(composite, object_id, is_full_delete = True):
    """
    Accepts a `composite` (dict respesenting `object_data` property of a composite object)
    and inserts a new deleted subobject.
    """
    composite["object_data"]["deleted_subobjects"].append({"object_id": object_id, "is_full_delete": is_full_delete})


def get_composite_subobject_object_data(object_id, object_type = None):
    """
    Returns a dict with object data to be used as composite subobject data.
    """
    return get_test_object_data(object_id, object_type=object_type)["object_data"]


# Fixed value and object data lists to be supplied into insert functions below
incorrect_object_values = [
    ("object_id", -1), ("object_id", "abc"),
    ("object_type", 1), ("object_type", "incorrect object type"),
    ("object_name", 123), ("object_name", ""), ("object_name", "a"*256),
    ("object_description", 1),
    ("is_published", 1), ("is_published", "str"), ("is_published", None),
    ("display_in_feed", 1), ("display_in_feed", "str"), ("display_in_feed", None),
    ("feed_timestamp", 1), ("feed_timestamp", True), ("feed_timestamp", None), ("feed_timestamp", "wrong str"), ("feed_timestamp", "99999-01-01"),
    ("show_description", 1), ("show_description", "str"), ("show_description", None),
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
    field_names = ("object_id", "object_type", "created_at", "modified_at", "object_name", "object_description", "is_published",
        "display_in_feed", "feed_timestamp", "show_description", "owner_id")
    query = "INSERT INTO %s" + str(field_names).replace("'", '"') + " VALUES " \
        + ", ".join(("(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" for _ in range(len(objects))))
    params = [AsIs("objects")]
    for o in objects:
        for field in field_names:
            if field == "feed_timestamp":
                value = parse_iso_timestamp(o[field], allow_empty_string=True)
                params.append(value)
            else:
                params.append(o[field])
    db_cursor.execute(query, params)


def insert_links(links, db_cursor):
    """
    Inserts link objects' data into the database.
    `links` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {"link": ...}}
    """
    field_names = ("object_id", "link", "show_description_as_link")
    query = "INSERT INTO %s" + str(field_names).replace("'", '"') + " VALUES " \
        + ", ".join(("(%s, %s, %s)" for _ in range(len(links))))
    params = [AsIs("links")]
    for l in links:
        params.append(l["object_id"])
        params.append(l["object_data"]["link"])
        params.append(l["object_data"]["show_description_as_link"])
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
    Inserts composite objects' data into the database (both composite properties and subobjects).
    `composite` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {...}}
    """
    field_names = ("object_id", "subobject_id", "column", "row", "selected_tab", "is_expanded", "show_description_composite", "show_description_as_link_composite")
    num_of_lines = sum((len(c["object_data"]["subobjects"]) for c in composite))
    query = "INSERT INTO %s" + str(field_names).replace("'", '"') + " VALUES " \
        + ", ".join(("(%s, %s, %s, %s, %s, %s, %s, %s)" for _ in range(num_of_lines)))
    params = [AsIs("composite")]
    for c in composite:
        for so in c["object_data"]["subobjects"]:
            params.append(c["object_id"])
            for field in field_names:
                if field == "object_id":
                    pass
                elif field == "subobject_id":
                    params.append(so["object_id"])
                else:
                    params.append(so[field])
    db_cursor.execute(query, params)

    # Insert composite_properties
    insert_composite_properties(composite, db_cursor)


def insert_composite_properties(composite, db_cursor):
    """
    Inserts composite properties into the database.
    `composite` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {...}}
    """
    field_names = ("object_id", "display_mode", "numerate_chapters")
    query = "INSERT INTO %s" + str(field_names).replace("'", '"') + " VALUES " \
        + ", ".join(("(%s, %s, %s)" for _ in range(len(composite))))
    params = [AsIs("composite_properties")]
    for c in composite:
        params.append(c["object_id"])
        params.append(c["object_data"]["display_mode"])
        params.append(c["object_data"]["numerate_chapters"])
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


object_data_insert_functions = {
    "link": insert_links,
    "markdown": insert_markdown,
    "to_do_list": insert_to_do_lists,
    "composite": insert_composite
}


# Sets of mock data insertions in the database
def insert_data_for_view_tests_non_published_objects(db_cursor, object_type = "link"):
    """
    Inserts another user and a set of objects in the database.
    Objects belong to different users and are partially published.
    If `object_type` is provided, inserted objects have it as their object type (defaults to "link").
    """
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user
    object_attributes = [get_test_object(i, object_type=object_type, 
        feed_timestamp=_get_object_feed_timestamp(i), # `feed_timestamp` is required for /objects/view test as admin
        owner_id=1, pop_keys=["object_data"]) for i in range(1, 11)]
    # object_attributes = get_objects_attributes_list(1, 10)
    for i in range(5, 10):
        object_attributes[i]["owner_id"] = 2
    for i in range(1, 10, 2):
        object_attributes[i]["is_published"] = True
    insert_objects(object_attributes, db_cursor)
    object_data_insert_functions[object_type]([get_test_object_data(i, object_type=object_type) for i in range(1, 11)], db_cursor)

    return {
        "inserted_object_ids": [i for i in range(1, 11)],
        "object_attributes": object_attributes
    }


def insert_data_for_view_tests_objects_with_non_published_tags(db_cursor, object_type = "link"):
    """
    Inserts published objects & object data of the provided `object_type`.
    Inserts published/non-published tags, marks all objects with published tags and some with non-published.
    """
    insert_objects([get_test_object(i, is_published=True, object_type=object_type, owner_id=1, pop_keys=["object_data"]) 
        for i in range(1, 11)], db_cursor) # Published objects
    insert_tags([get_test_tag(i, is_published=i<3) for i in range(1, 5)], db_cursor) # Published & non-published tags
    insert_objects_tags([i for i in range(1, 11)], [1, 2], db_cursor)  # Tag objects with published tags
    insert_objects_tags([i for i in range(6, 11)], [3], db_cursor)  # Tag objects with non-published tags
    insert_objects_tags([i for i in range(9, 11)], [4], db_cursor)
    object_data_insert_functions[object_type]([get_test_object_data(i, object_type=object_type) for i in range(1, 11)], db_cursor)

    return {
        "inserted_object_ids": [i for i in range(1, 11)],
        "expected_object_ids_as_anonymous": [i for i in range(1, 6)]
    }


def insert_data_for_composite_view_tests_objects_with_non_published_tags(db_cursor):
    insert_objects([    # Composite objects & link subobject
        get_test_object(1, object_type="link", is_published=True, owner_id=1, pop_keys=["object_data"]),
        get_test_object(11, object_type="composite", is_published=True, owner_id=1, pop_keys=["object_data"]),
        get_test_object(12, object_type="composite", is_published=True, owner_id=1, pop_keys=["object_data"]),
        get_test_object(13, object_type="composite", is_published=True, owner_id=1, pop_keys=["object_data"])
    ], db_cursor)
    insert_composite([get_test_object_data(i, object_type="composite") for i in range (11, 14)], db_cursor) # Object data
    insert_tags([   # Published & non-published tags
        get_test_tag(1, is_published=True), get_test_tag(2, is_published=True),
        get_test_tag(3, is_published=False), get_test_tag(4, is_published=False)
    ], db_cursor)
    insert_objects_tags([11, 12, 13], [1, 2], db_cursor)   # Objects tags
    insert_objects_tags([12, 13], [3], db_cursor)
    insert_objects_tags([13], [4], db_cursor)


def insert_data_for_update_tests(db_cursor):
    obj_list = [get_test_object(1, owner_id=1, pop_keys=["object_data"]), get_test_object(2, owner_id=1, pop_keys=["object_data"])]
    l_list = [get_test_object_data(1), get_test_object_data(2)]
    insert_objects(obj_list, db_cursor)
    insert_links(l_list, db_cursor)


def insert_data_for_delete_tests(db_cursor):
    obj_list = [get_test_object(1, owner_id=1, pop_keys=["object_data"]), get_test_object(2, owner_id=1, pop_keys=["object_data"]),
        get_test_object(3, owner_id=1, pop_keys=["object_data"])]
    l_list = [get_test_object_data(1), get_test_object_data(2), get_test_object_data(3)]
    insert_objects(obj_list, db_cursor)
    insert_links(l_list, db_cursor)


def insert_non_cyclic_hierarchy(db_cursor, root_is_published = True, root_has_non_published_tag = False):
    """
    Inserts a non-cyclic hierarchy for testing correct requests.

    Hierarchy structure:
    - 99999 (composite):
        - 1 (composite):
            - 11 (composite):
                - 111 (link);
                - 112 (link);
            - 12 (link);
        - 2 (composite):
            - 21 (composite, no subobjects);
            - 22 (composite):
                - 221 (link);
        - 3 (link);
        - 4 (markdown);
        - 5 (to-do list);
    """
    # `objects` table
    obj_list = [
        get_test_object(99999, owner_id=1, object_type="composite", is_published=root_is_published, pop_keys=["object_data"]),
        get_test_object(1, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(11, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(111, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(112, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(12, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(2, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(21, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(22, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(221, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(3, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(4, owner_id=1, object_type="markdown", pop_keys=["object_data"]),
        get_test_object(5, owner_id=1, object_type="to_do_list", pop_keys=["object_data"]),
    ]

    insert_objects(obj_list, db_cursor)

    # `composite` table
    composite_object_data = []

    d = get_test_object_data(99999, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1)
    add_composite_subobject(d, object_id=2)
    add_composite_subobject(d, object_id=3)
    add_composite_subobject(d, object_id=4)
    add_composite_subobject(d, object_id=5)
    composite_object_data.append(d)

    d = get_test_object_data(1, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=11)
    add_composite_subobject(d, object_id=12)
    composite_object_data.append(d)

    d = get_test_object_data(11, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=111)
    add_composite_subobject(d, object_id=112)
    composite_object_data.append(d)

    d = get_test_object_data(2, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=21)
    add_composite_subobject(d, object_id=22)
    composite_object_data.append(d)

    d = get_test_object_data(22, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=221)
    composite_object_data.append(d)

    insert_composite(composite_object_data, db_cursor)

    # Add optional non-published tag for root object
    if root_has_non_published_tag:
        insert_tags([get_test_tag(1, is_published=False)], db_cursor)
        insert_objects_tags([99999], [1], db_cursor)

    # Return expected results
    return {
        "composite": [99999, 1, 11, 2, 21, 22],
        "non_composite": [111, 112, 12, 221, 3, 4, 5]
    }


def insert_non_cyclic_hierarchy_with_max_depth_exceeded(db_cursor):
    """
    Inserts a non-cyclic hierarchy for testing correct requests. 
    Actual hierarchy depth is bigger than the depth that should be checked by the route handler.

    Hierarchy structure:
    - 99999 (composite):
        - 1 (composite):
            - 11 (composite):
                - 111 (composite):
                    - 1111 (composite):
                        - 11111 (composite):
                            - 111111 (composite):   # expected not to be returned because of hierarchy depth limit
                                - 1111111 (link);   # expected not to be returned because of hierarchy depth limit
                                - 3 (link);
                        - 11112 (link);
                    - 1112 (link);
                - 112 (link);
            - 12 (link);
        - 2 (composite):
            - 21 (composite, no subobjects);
            - 22 (composite):
                - 221 (link);
        - 3 (link);
        - 4 (markdown);
        - 5 (to-do list);
    """
    # `objects` table
    obj_list = [
        get_test_object(99999, owner_id=1, object_type="composite", is_published=True, pop_keys=["object_data"]),
        get_test_object(1, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(11, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(111, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(1111, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(11111, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(111111, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(1111111, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(3, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(11112, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(1112, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(112, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(12, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(2, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(21, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(22, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(221, owner_id=1, object_type="link", pop_keys=["object_data"]),
        # get_test_object(3, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(4, owner_id=1, object_type="markdown", pop_keys=["object_data"]),
        get_test_object(5, owner_id=1, object_type="to_do_list", pop_keys=["object_data"]),
    ]

    insert_objects(obj_list, db_cursor)

    # `composite` table
    composite_object_data = []

    d = get_test_object_data(99999, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1)
    add_composite_subobject(d, object_id=2)
    add_composite_subobject(d, object_id=3)
    add_composite_subobject(d, object_id=4)
    add_composite_subobject(d, object_id=5)
    composite_object_data.append(d)

    d = get_test_object_data(1, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=11)
    add_composite_subobject(d, object_id=12)
    composite_object_data.append(d)

    d = get_test_object_data(11, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=111)
    add_composite_subobject(d, object_id=112)
    composite_object_data.append(d)

    d = get_test_object_data(111, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1111)
    add_composite_subobject(d, object_id=1112)
    composite_object_data.append(d)

    d = get_test_object_data(1111, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=11111)
    add_composite_subobject(d, object_id=11112)
    composite_object_data.append(d)

    d = get_test_object_data(11111, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=111111)
    composite_object_data.append(d)

    d = get_test_object_data(111111, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1111111)
    add_composite_subobject(d, object_id=3)
    composite_object_data.append(d)

    d = get_test_object_data(2, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=21)
    add_composite_subobject(d, object_id=22)
    composite_object_data.append(d)

    d = get_test_object_data(22, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=221)
    composite_object_data.append(d)

    insert_composite(composite_object_data, db_cursor)

    # Return expected results
    return {
        "composite": [99999, 1, 11, 111, 1111, 11111, 2, 21, 22],
        "non_composite": [11112, 1112, 112, 12, 221, 3, 4, 5]
    }


def insert_a_cyclic_hierarchy(db_cursor):
    """
    Inserts a hierarchy with cyclic references and multiple occurence of the same composite object for testing correct requests.

    Hierarchy structure:
    - 99999 (composite):
        - 1 (composite):
            - 11 (composite):
                - 111 (composite):
                    - 1 (composite, cyclic reference);
                - 112 (link);
            - 12 (link);
        - 2 (composite):
            - 21 (composite, no subobjects);
            - 22 (composite):
                - 221 (link);
                - 21 (composite, second non-cyclic reference);
        - 3 (link);
        - 4 (markdown);
        - 5 (to-do list);
    """
    # `objects` table
    obj_list = [
        get_test_object(99999, owner_id=1, object_type="composite", is_published=True, pop_keys=["object_data"]),
        get_test_object(1, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(11, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(111, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(112, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(12, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(2, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(21, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(22, owner_id=1, object_type="composite", pop_keys=["object_data"]),
        get_test_object(221, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(3, owner_id=1, object_type="link", pop_keys=["object_data"]),
        get_test_object(4, owner_id=1, object_type="markdown", pop_keys=["object_data"]),
        get_test_object(5, owner_id=1, object_type="to_do_list", pop_keys=["object_data"]),
    ]

    insert_objects(obj_list, db_cursor)

    # `composite` table
    composite_object_data = []

    d = get_test_object_data(99999, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1)
    add_composite_subobject(d, object_id=2)
    add_composite_subobject(d, object_id=3)
    add_composite_subobject(d, object_id=4)
    add_composite_subobject(d, object_id=5)
    composite_object_data.append(d)

    d = get_test_object_data(1, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=11)
    add_composite_subobject(d, object_id=12)
    composite_object_data.append(d)

    d = get_test_object_data(11, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=111)
    add_composite_subobject(d, object_id=112)
    composite_object_data.append(d)

    d = get_test_object_data(111, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=1)
    composite_object_data.append(d)

    d = get_test_object_data(2, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=21)
    add_composite_subobject(d, object_id=22)
    composite_object_data.append(d)

    d = get_test_object_data(22, object_type="composite")
    d["object_data"]["subobjects"] = []
    add_composite_subobject(d, object_id=221)
    add_composite_subobject(d, object_id=21)
    composite_object_data.append(d)

    insert_composite(composite_object_data, db_cursor)

    # Return expected results
    return {
        "composite": [99999, 1, 11, 111, 2, 21, 22],
        "non_composite": [112, 12, 221, 3, 4, 5]
    }
