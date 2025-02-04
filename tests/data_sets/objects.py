from datetime import datetime

from tests.data_generators.objects import get_object_attrs, get_test_object_data, get_composite_subobject_data
from tests.data_generators.tags import get_test_tag
from tests.data_generators.users import get_test_user

from tests.db_operations.objects import insert_objects, object_data_insert_functions, insert_links, \
    insert_composite
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags
from tests.db_operations.users import insert_users


# Incorrect and unallowed object attributes for /objects/add & /objects/update routes
incorrect_object_attributes = {
    "object_id": [None, False, "str", {}, [], -1],
    "object_type": [None, False, 1, {}, [], "wrong str"],
    "object_name": [None, False, 1, {}, [], "", "a" * 256],
    "object_description": [None, False, 1, {}, []],
    "is_published": [None, "str", 1, {}, []],
    "display_in_feed": [None, "str", 1, {}, []],
    "feed_timestamp": [1, {}, [], "wrong str", "99999-01-01"],
    "show_description": [None, "str", 1, {}, []],
    "owner_id": [None, False, "str", {}, [], -1],
    "object_data": [None, False, "str", 1, []],    
    "unallowed": ["unallowed"]
}

incorrect_link_attributes = {
    "link": [None, False, 1, "wrong str", [], {}],
    "show_description_as_link": [None, 1, "str", [], {}],
    "unallowed": ["unallowed"]
}

incorrect_markdown_attributes = {
    "raw_text": [None, False, 1, [], {}, ""],
    "unallowed": ["unallowed"]
}

incorrect_to_do_list_attributes = {
    "sort_type": [None, False, 1, {}, [], "wrong str"],
    "items": [None, False, 1, "str", {}, []],
    "unallowed": ["unallowed"]
}

incorrect_to_do_list_item_attributes = {
    "item_number": [None, False, "str", [], {}, -1],
    "item_state": [None, False, 1, [], {}, "wrong str"],
    "item_text": [None, False, 0, [], {}],
    "commentary": [None, False, 0, [], {}],
    "indent": [None, False, "str", [], {}, -1],
    "is_expanded": [None, "str", 1, [], {}],
    "unallowed": ["unallowed"]
}


links_data_list = [{
        "object_id": x,
        "object_data": get_test_object_data(x, object_type="link")["object_data"]
    } for x in range(1, 11)
]


markdown_data_list = [{
        "object_id": x,
        "object_data": get_test_object_data(x, object_type="markdown")["object_data"]
    } for x in range(11, 21)
]


to_do_lists_data_list = [{
        "object_id": x,
        "object_data": get_test_object_data(x, object_type="to_do_list")["object_data"]
    } for x in range(21, 31)
]


composite_data_list = [{
        "object_id": x,
        "object_data": get_test_object_data(x, object_type="composite")["object_data"]
    } for x in range(31, 41)
]


def insert_objects_update_tags_test_data(db_cursor):
    """
    Inserts objects [1, 2], tags [1...10] and adds tags [1...5] to both objects.

    Objects' modification time is set to 01.01.2001 00:00:00.
    """
    insert_objects([
        get_object_attrs(i, modified_at=datetime(2001, 1, 1))
    for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 11)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1, 2, 3, 4, 5], db_cursor)


def insert_data_for_view_tests_non_published_objects(db_cursor, object_type = "link"):
    """
    Inserts another user and a set of objects in the database.
    Objects belong to different users and are partially published.
    If `object_type` is provided, inserted objects have it as their object type (defaults to "link").
    """
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor) # add a regular user
    object_attributes = [get_object_attrs(i, object_type=object_type) for i in range(1, 11)]
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
    insert_objects([get_object_attrs(i, is_published=True, object_type=object_type)
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
        get_object_attrs(1, object_type="link", is_published=True),
        get_object_attrs(11, object_type="composite", is_published=True),
        get_object_attrs(12, object_type="composite", is_published=True),
        get_object_attrs(13, object_type="composite", is_published=True)
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
    obj_list = [get_object_attrs(1), get_object_attrs(2)]
    l_list = [get_test_object_data(1), get_test_object_data(2)]
    insert_objects(obj_list, db_cursor)
    insert_links(l_list, db_cursor)


def insert_data_for_delete_tests(db_cursor):
    obj_list = [get_object_attrs(i) for i in range(1, 4)]
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
        get_object_attrs(99999, object_type="composite", is_published=root_is_published),
        get_object_attrs(1, object_type="composite"),
        get_object_attrs(11, object_type="composite"),
        get_object_attrs(111, object_type="link"),
        get_object_attrs(112, object_type="link"),
        get_object_attrs(12, object_type="link"),
        get_object_attrs(2, object_type="composite"),
        get_object_attrs(21, object_type="composite"),
        get_object_attrs(22, object_type="composite"),
        get_object_attrs(221, object_type="link"),
        get_object_attrs(3, object_type="link"),
        get_object_attrs(4, object_type="markdown"),
        get_object_attrs(5, object_type="to_do_list"),
    ]

    insert_objects(obj_list, db_cursor)

    # `composite` table
    composite_object_data = []

    d = get_test_object_data(99999, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(1, 0, 0),
        get_composite_subobject_data(2, 0, 1),
        get_composite_subobject_data(3, 0, 2),
        get_composite_subobject_data(4, 0, 3),
        get_composite_subobject_data(5, 0, 4)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(1, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(11, 0, 0),
        get_composite_subobject_data(12, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(11, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(111, 0, 0),
        get_composite_subobject_data(112, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(2, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(21, 0, 0),
        get_composite_subobject_data(22, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(22, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(221, 0, 0)
    ]
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
        get_object_attrs(99999, object_type="composite", is_published=True),
        get_object_attrs(1, object_type="composite"),
        get_object_attrs(11, object_type="composite"),
        get_object_attrs(111, object_type="composite"),
        get_object_attrs(1111, object_type="composite"),
        get_object_attrs(11111, object_type="composite"),
        get_object_attrs(111111, object_type="composite"),
        get_object_attrs(1111111, object_type="link"),
        get_object_attrs(3, object_type="link"),
        get_object_attrs(11112, object_type="link"),
        get_object_attrs(1112, object_type="link"),
        get_object_attrs(112, object_type="link"),
        get_object_attrs(12, object_type="link"),
        get_object_attrs(2, object_type="composite"),
        get_object_attrs(21, object_type="composite"),
        get_object_attrs(22, object_type="composite"),
        get_object_attrs(221, object_type="link"),
        # get_object_attrs(3, object_type="link"),
        get_object_attrs(4, object_type="markdown"),
        get_object_attrs(5, object_type="to_do_list"),
    ]

    insert_objects(obj_list, db_cursor)

    # `composite` table
    composite_object_data = []

    d = get_test_object_data(99999, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(1, 0, 0),
        get_composite_subobject_data(2, 0, 1),
        get_composite_subobject_data(3, 0, 2),
        get_composite_subobject_data(4, 0, 3),
        get_composite_subobject_data(5, 0, 4)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(1, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(11, 0, 0),
        get_composite_subobject_data(12, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(11, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(111, 0, 0),
        get_composite_subobject_data(112, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(111, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(1111, 0, 0),
        get_composite_subobject_data(1112, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(1111, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(11111, 0, 0),
        get_composite_subobject_data(11112, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(11111, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(111111, 0, 0)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(111111, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(111111, 0, 0),
        get_composite_subobject_data(3, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(2, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(21, 0, 0),
        get_composite_subobject_data(22, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(22, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(221, 0, 0)
    ]
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
        get_object_attrs(99999, object_type="composite", is_published=True),
        get_object_attrs(1, object_type="composite"),
        get_object_attrs(11, object_type="composite"),
        get_object_attrs(111, object_type="composite"),
        get_object_attrs(112, object_type="link"),
        get_object_attrs(12, object_type="link"),
        get_object_attrs(2, object_type="composite"),
        get_object_attrs(21, object_type="composite"),
        get_object_attrs(22, object_type="composite"),
        get_object_attrs(221, object_type="link"),
        get_object_attrs(3, object_type="link"),
        get_object_attrs(4, object_type="markdown"),
        get_object_attrs(5, object_type="to_do_list"),
    ]

    insert_objects(obj_list, db_cursor)

    # `composite` table
    composite_object_data = []

    d = get_test_object_data(99999, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(1, 0, 0),
        get_composite_subobject_data(2, 0, 1),
        get_composite_subobject_data(3, 0, 2),
        get_composite_subobject_data(4, 0, 3),
        get_composite_subobject_data(5, 0, 4)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(1, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(11, 0, 0),
        get_composite_subobject_data(12, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(11, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(111, 0, 0),
        get_composite_subobject_data(112, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(111, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(1, 0, 0)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(2, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(21, 0, 0),
        get_composite_subobject_data(22, 0, 1)
    ]
    composite_object_data.append(d)

    d = get_test_object_data(22, object_type="composite")
    d["object_data"]["subobjects"] = [
        get_composite_subobject_data(221, 0, 0),
        get_composite_subobject_data(21, 0, 1)
    ]
    composite_object_data.append(d)

    insert_composite(composite_object_data, db_cursor)

    # Return expected results
    return {
        "composite": [99999, 1, 11, 111, 2, 21, 22],
        "non_composite": [112, 12, 221, 3, 4, 5]
    }
