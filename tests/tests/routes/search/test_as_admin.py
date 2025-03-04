"""
Basic search, pagination and ranking tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 5)))
    from tests.util import run_pytest_tests

from random import shuffle

from tests.data_generators.objects import get_test_object, get_object_attrs
from tests.data_generators.searchables import get_test_searchable
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.searchables import insert_searchables
from tests.db_operations.tags import insert_tags

from tests.request_generators.search import get_search_request_body
from tests.request_generators.tags import get_tags_add_request_body

from tests.util import wait_for


async def test_incorrect_request_body(cli_with_search, db_cursor):
    # Invalid JSON & missing top-level attribute
    for body in ["not a JSON document", {}]:
        resp = await cli_with_search.post("/search", data=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect & unallowed top-level attributes
    incorrect_attributes = {
        "query": [None, False, 1, "str", []],
        "unallowed": ["unallowed"]
    }
    for attr, values in incorrect_attributes.items():
        for value in values:
            body = get_search_request_body()
            body[attr] = value
            resp = await cli_with_search.post("/search", data=body, headers=headers_admin_token)
            assert resp.status == 400
    
    # Missing query attributes
    for attr in ["query_text", "page", "items_per_page"]:
        body = get_search_request_body()
        body["query"].pop(attr)
        resp = await cli_with_search.post("/search", data=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect & unallowed query attributes
    incorrect_query_attributes = {
        "query_text": [None, False, 1, [], {}, "", "a" * 256],
        "page": [None, False, "a", [], {}, -1, 0],
        "items_per_page": [None, False, "a", [], {}, -1, 0],
        "unallowed": ["unallowed"]
    }
    for attr, values in incorrect_query_attributes.items():
        for value in values:
            body = get_search_request_body()
            body["query"][attr] = value
            resp = await cli_with_search.post("/search", data=body, headers=headers_admin_token)
            assert resp.status == 400


async def test_correct_search_published_objects_and_tags(cli_with_search, db_cursor):
    # Insert mock data
    obj_list = [get_object_attrs(i + 1, is_published=True) for i in range(10)]
    insert_objects(obj_list, db_cursor)

    searchables = [get_test_searchable(object_id=i + 1, text_a="word" if i < 5 else "bird") for i in range(10)]
    insert_searchables(searchables, db_cursor)

    tag_list = [get_test_tag(i + 1, is_published=True) for i in range(10)]
    insert_tags(tag_list, db_cursor)

    searchables = [get_test_searchable(tag_id=i + 1, text_a="bird" if i < 5 else "word") for i in range(10)]
    insert_searchables(searchables, db_cursor)

    # Check if matching tags and objects are returned
    body = get_search_request_body()
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 5 + 5

    object_ids = [item["item_id"] for item in resp_json["items"] if item["item_type"] == "object"]
    assert sorted(object_ids) == [i + 1 for i in range(5)]

    tag_ids = [item["item_id"] for item in resp_json["items"] if item["item_type"] == "tag"]
    assert sorted(tag_ids) == [i for i in range(6, 11)]


async def test_correct_search_non_published_objects(cli_with_search, db_cursor):
    # Insert mock data
    obj_list = [get_object_attrs(i + 1, is_published=bool(i % 2)) for i in range(20)]
    insert_objects(obj_list, db_cursor)

    searchables = [get_test_searchable(object_id=i + 1, text_a="word" if i < 10 else "bird") for i in range(20)]
    insert_searchables(searchables, db_cursor)

    # Check if matching objects are returned, regardless of their `is_published` prop
    body = get_search_request_body()
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 10

    object_ids = [item["item_id"] for item in resp_json["items"] if item["item_type"] == "object"]
    assert sorted(object_ids) == [i for i in range(1, 11)]


async def test_correct_search_non_published_tags(cli_with_search, db_cursor):
    tag_list = [get_test_tag(i + 1, is_published=bool(i % 2)) for i in range(20)]
    insert_tags(tag_list, db_cursor)

    searchables = [get_test_searchable(tag_id=i + 1, text_a="word" if i < 10 else "bird") for i in range(10)]
    insert_searchables(searchables, db_cursor)

    # Check if matching tags are returned, regardless of their `is_published` prop
    body = get_search_request_body()
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 10

    tag_ids = [item["item_id"] for item in resp_json["items"] if item["item_type"] == "tag"]
    assert sorted(tag_ids) == [i for i in range(1, 11)]


async def test_correct_search_objects_with_non_published_tags(cli_with_search, db_cursor):
    # Insert mock data
    obj_list = [get_object_attrs(i + 1, is_published=bool(i % 2)) for i in range(20)]
    insert_objects(obj_list, db_cursor)

    searchables = [get_test_searchable(object_id=i + 1, text_a="word" if i < 10 else "bird") for i in range(20)]
    insert_searchables(searchables, db_cursor)

    tag_list = [get_test_tag(i + 1, is_published=bool(i < 1)) for i in range(3)]
    insert_tags(tag_list, db_cursor)

    searchables = [get_test_searchable(tag_id=i + 1, text_a="bird") for i in range(3)]
    insert_searchables(searchables, db_cursor)

    insert_objects_tags([i for i in range(1, 11)], [1], db_cursor)
    insert_objects_tags([i for i in range(6, 11)], [2], db_cursor)
    insert_objects_tags([i for i in range(9, 11)], [3], db_cursor)

    # Check if matching objects are returned, regardless of being published or tagged with non-published tags
    body = get_search_request_body()
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 10

    object_ids = [item["item_id"] for item in resp_json["items"] if item["item_type"] == "object"]
    assert sorted(object_ids) == [i for i in range(1, 11)]


async def test_search_without_match(cli_with_search, db_cursor):
    # Insert mock data
    obj_list = [get_object_attrs(i + 1) for i in range(10)]
    insert_objects(obj_list, db_cursor)

    searchables = [get_test_searchable(object_id=i + 1, text_a="bird") for i in range(10)]
    insert_searchables(searchables, db_cursor)

    body = get_search_request_body()
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 404


async def test_pagination_and_basic_ranking(cli_with_search, db_cursor):
    # Insert mock data
    obj_list = [get_object_attrs(i + 1) for i in range(20)]
    insert_objects(obj_list, db_cursor)

    searchables = []
    for i in range(20):
        # Get different combinations of matching & non-matching words for each object
        # Objects have more matching words if they have a bigger `object_id` value
        words = ["word" for _ in range (i + 1)]
        words.extend(["bird" for _ in range(20 - i - 1)])
        shuffle(words)
        text_a = " ".join(words)
        searchables.append(get_test_searchable(object_id=i + 1, text_a=text_a))
    
    insert_searchables(searchables, db_cursor)

    # Query different pages and check if expected object IDs are returned
    for i in range(10):
        body = get_search_request_body(page=i + 1, items_per_page=2)
        resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
        assert resp.status == 200
        resp_json = await resp.json()

        assert resp_json["total_items"] == 20

        object_ids = [item["item_id"] for item in resp_json["items"]]
        assert object_ids == [20 - 2 * i, 20 - 2 * i - 1]
    
    # Query non-existing page
    body = get_search_request_body(page=11, items_per_page=2)
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 404


async def test_ranking_tag_name_description(cli_with_search, db_cursor):
    # Add tags
    for tag_name, tag_description in [("bird cake", "word"), ("word", "# bird bird")]: # search "word" => 2 > 1; search "bird" => 2 > 1
        body = get_tags_add_request_body(tag_name=tag_name, tag_description=tag_description)
        resp = await cli_with_search.post("/tags/add", json=body, headers=headers_admin_token)
        assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables")
        return db_cursor.fetchone()[0] == 2
    
    await wait_for(fn, msg="Tag searchables were not processed in time.")

    # Check if tag_name has more priority than non-header tag_description
    body = get_search_request_body(items_per_page=10)
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 2
    item_ids = [item["item_id"] for item in resp_json["items"]]
    assert item_ids == [2, 1]

    # Check if tag_name has equal priority with tag_description
    body = get_search_request_body(query_text="bird", items_per_page=10)
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 2
    item_ids = [item["item_id"] for item in resp_json["items"]]
    assert item_ids == [2, 1]


async def test_ranking_object_name_description(cli_with_search, db_cursor):
    # Add objects
    for object_name, object_description in [("bird cake", "word"), ("word", "# bird bird")]: # search "word" => 2 > 1; search "bird" => 2 > 1
        object = get_test_object(1, object_name=object_name, object_description=object_description, pop_keys=["object_id", "created_at", "modified_at"])
        resp = await cli_with_search.post("/objects/add", json={"object": object}, headers=headers_admin_token)
        assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables")
        return db_cursor.fetchone()[0] == 2
    
    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if object_name has more priority than non-header object_description
    body = get_search_request_body(items_per_page=10)
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 2
    item_ids = [item["item_id"] for item in resp_json["items"]]
    assert item_ids == [2, 1]

    # Check if object_name has equal priority with object_description
    body = get_search_request_body(query_text="bird", items_per_page=10)
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 2
    item_ids = [item["item_id"] for item in resp_json["items"]]
    assert item_ids == [2, 1]


async def test_ranking_object_name_link(cli_with_search, db_cursor):
    # Add objects
    object = get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])
    object["object_data"]["link"] = "https://wikipedia.org"
    resp = await cli_with_search.post("/objects/add", json={"object": object}, headers=headers_admin_token)
    assert resp.status == 200
    
    object = get_test_object(1, object_name="https://wikipedia.org", pop_keys=["object_id", "created_at", "modified_at"])
    resp = await cli_with_search.post("/objects/add", json={"object": object}, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables")
        return db_cursor.fetchone()[0] == 2
    
    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if object_name has more priority than link object data
    body = get_search_request_body(query_text="wikipedia.org", items_per_page=10)
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 2
    item_ids = [item["item_id"] for item in resp_json["items"]]
    assert item_ids == [2, 1]


async def test_ranking_object_name_markdown(cli_with_search, db_cursor):
    # Add objects
    # search "word" => 2 > 1; search "bird" => 2 > 1
    object = get_test_object(1, object_type="markdown", pop_keys=["object_id", "created_at", "modified_at"])
    object["object_name"] = "bird cake"
    object["object_data"]["raw_text"] = "word"
    resp = await cli_with_search.post("/objects/add", json={"object": object}, headers=headers_admin_token)
    assert resp.status == 200
    
    object = get_test_object(1, object_type="markdown", pop_keys=["object_id", "created_at", "modified_at"])
    object["object_name"] = "word"
    object["object_data"]["raw_text"] = "# bird bird"
    resp = await cli_with_search.post("/objects/add", json={"object": object}, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables")
        return db_cursor.fetchone()[0] == 2
    
    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if object_name has more priority than non-header markdown object data
    body = get_search_request_body(items_per_page=10)
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 2
    item_ids = [item["item_id"] for item in resp_json["items"]]
    assert item_ids == [2, 1]

    # Check if object_name has equal priority with headers in markdown object data
    body = get_search_request_body(query_text="bird", items_per_page=10)
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 2
    item_ids = [item["item_id"] for item in resp_json["items"]]
    assert item_ids == [2, 1]


async def test_ranking_object_name_to_do_list_item_and_comment(cli_with_search, db_cursor):
    # Add objects
    # search "word" => 2 > 1; search "bird" => 2 > 1
    object = get_test_object(1, object_type="to_do_list", pop_keys=["object_id", "created_at", "modified_at"])
    # object["object_name"] = "bird"
    object["object_data"]["items"] = [{"item_number": 1, "item_state": "active", "item_text": "word", "commentary": "bird", "indent": 0, "is_expanded": True }]
    resp = await cli_with_search.post("/objects/add", json={"object": object}, headers=headers_admin_token)
    assert resp.status == 200
    
    object = get_test_object(1, object_type="to_do_list", pop_keys=["object_id", "created_at", "modified_at"])
    object["object_name"] = "word"
    object["object_data"]["items"] = [{"item_number": 1, "item_state": "active", "item_text": "bird", "commentary": "", "indent": 0, "is_expanded": True }]
    resp = await cli_with_search.post("/objects/add", json={"object": object}, headers=headers_admin_token)
    assert resp.status == 200

    # Wait for object searchables to be added
    def fn():
        db_cursor.execute("SELECT COUNT(*) FROM searchables")
        return db_cursor.fetchone()[0] == 2
    
    await wait_for(fn, msg="Object searchables were not processed in time.")

    # Check if object_name has more priority than to-do list item text
    body = get_search_request_body(items_per_page=10)
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 2
    item_ids = [item["item_id"] for item in resp_json["items"]]
    assert item_ids == [2, 1]

    # Check if to-do list item text has more priority than to-do list item commentary
    body = get_search_request_body(query_text="bird", items_per_page=10)
    resp = await cli_with_search.post("/search", json=body, headers=headers_admin_token)
    assert resp.status == 200
    resp_json = await resp.json()

    assert resp_json["total_items"] == 2
    item_ids = [item["item_id"] for item in resp_json["items"]]
    assert item_ids == [2, 1]


if __name__ == "__main__":
    run_pytest_tests(__file__)
