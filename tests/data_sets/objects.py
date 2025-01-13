from datetime import datetime

from tests.data_generators.objects import get_test_object, get_test_object_data, add_composite_subobject
from tests.data_generators.tags import get_test_tag
from tests.data_generators.users import get_test_user

from tests.db_operations.objects import insert_objects, object_data_insert_functions, insert_links, \
    insert_composite
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags
from tests.db_operations.users import insert_users



# Fixed value and object data lists to be supplied into insert functions below
incorrect_object_values = [
    ("object_id", -1), ("object_id", "abc"),
    ("object_type", 1), ("object_type", "incorrect object type"),
    ("object_name", 123), ("object_name", ""), ("object_name", "a"*256),
    ("object_description", 1),
    ("is_published", 1), ("is_published", "str"), ("is_published", None),
    ("display_in_feed", 1), ("display_in_feed", "str"), ("display_in_feed", None),
    ("feed_timestamp", 1), ("feed_timestamp", True), ("feed_timestamp", "wrong str"), ("feed_timestamp", "99999-01-01"),
    ("show_description", 1), ("show_description", "str"), ("show_description", None),
    ("owner_id", -1), ("owner_id", "str"), ("owner_id", True),
    ("object_data", None), ("object_data", ""), ("object_data", 1)
]


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
        get_test_object(i, owner_id=1, modified_at=datetime(2001, 1, 1), pop_keys=["object_data"])
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
    object_attributes = [get_test_object(i, object_type=object_type, owner_id=1, pop_keys=["object_data"]) for i in range(1, 11)]
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
