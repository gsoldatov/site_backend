"""
Tests for object tagging in /objects/... and /tags/... routes.
"""

import os
# import json
# from datetime import datetime
# from copy import deepcopy

import pytest
from psycopg2.extensions import AsIs

# from util import check_ids
from fixtures.app import *
from fixtures.tags import insert_tags, tag_list
from fixtures.objects import get_test_object_link, insert_objects
from fixtures.objects_tags import insert_objects_tags


async def test_objects_add(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    schema = config["db"]["db_schema"]

    # Insert mock data
    insert_tags(tag_list, db_cursor, config, generate_tag_ids = True)

    # Incorrect object's tags
    for added_tags in ["not a list", 1, {}]:
        link = get_test_object_link(1, ["object_id", "created_at", "modified_at"])
        link["added_tags"] = added_tags
        resp = await cli.post("/objects/add", json = {"object": link})
        assert resp.status == 400

    # Add non-existing tag by tag_id (and get a 400 error)
    link = get_test_object_link(1, ["object_id", "created_at", "modified_at"])
    link["added_tags"] = [1, 100]
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400

    # Add existing tags by tag_id and tag_name (and check duplicate tag_ids handling)
    link = get_test_object_link(1, ["object_id", "created_at", "modified_at"])
    link["added_tags"] = ["a0", 1, "b1", 2, 9, 10]
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 9, 10] # "a0", "b1", 9, 10
    cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in cursor.fetchall()]) == [1, 2, 9, 10]
    
    # Add non-existing tags by tag_name (and check duplicate tag_name handling)
    link = get_test_object_link(2, ["object_id", "created_at", "modified_at"])
    link["added_tags"] = ["a0", 2, 3, 4, "New Tag", "New Tag 2", "new tag"]
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [1, 2, 3, 4, 11, 12] # "a0", 2, 3, 4, "new tag", "new tag 2"
    cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in cursor.fetchall()]) == [1, 2, 3, 4, 11, 12]
    cursor.execute(f"SELECT tag_name FROM {schema}.tags WHERE tag_name = 'New Tag' OR tag_name = 'New Tag 2'")
    assert sorted([r[0] for r in cursor.fetchall()]) == ["New Tag", "New Tag 2"]


async def test_objects_update(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    schema = config["db"]["db_schema"]

    # Insert mock data
    insert_tags(tag_list, db_cursor, config, generate_tag_ids = True)
    insert_objects([get_test_object_link(1, ["object_data"])], db_cursor, config)
    insert_objects_tags([1], [1, 2, 3, 4, 5], db_cursor, config)
    
    # Incorrect added_tags and removed_tag_ids
    for added_tags in ["not a list", 1, {}]:
        link = get_test_object_link(1, ["created_at", "modified_at", "object_type"])
        link["added_tags"] = added_tags
        resp = await cli.put("/objects/update", json = {"object": link})
        assert resp.status == 400
    
    for removed_tag_ids in ["not a list", 1, {}]:
        link = get_test_object_link(1, ["created_at", "modified_at", "object_type"])
        link["removed_tag_ids"] = removed_tag_ids
        resp = await cli.put("/objects/update", json = {"object": link})
        assert resp.status == 400
    
    # Add non-existing tag by tag_id (and get a 400 error)
    link = get_test_object_link(1, ["created_at", "modified_at", "object_type"])
    link["added_tags"] = [1, 100]
    resp = await cli.put("/objects/update", json = {"object": link})
    assert resp.status == 400

    # Add existing tags by tag_id and tag_name (check duplicates in request handling (added once) and retagging with the same tags (tag is reapplied))
    link = get_test_object_link(1, ["created_at", "modified_at", "object_type"])
    link["added_tags"] = ["a0", 1, "b1", 2, "i0", 10]
    resp = await cli.put("/objects/update", json = {"object": link})
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 9, 10] # "i0", 10 were added; 1, 2 were reapplied 
                                                  # (and should be returned for the case with partially applied tags in route with multiple objects being tagged)
    cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in cursor.fetchall()]) == [1, 2, 3, 4, 5, 9, 10]

    # Add non-existing tags by tag_name (and check duplicate tag_name handling) + remove existing tags
    link = get_test_object_link(1, ["created_at", "modified_at", "object_type"])
    link["added_tags"] = ["a0", 2, "New Tag", "New Tag 2", "new tag"]
    link["removed_tag_ids"] = [9, 10]
    resp = await cli.put("/objects/update", json = {"object": link})
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [1, 2, 11, 12] # 1, 2 were reapplied; "New Tag", "New Tag 2"
    cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in cursor.fetchall()]) == [1, 2, 3, 4, 5, 11, 12] # 9, 10 were removed; 11, 12 were added
    cursor.execute(f"SELECT tag_name FROM {schema}.tags WHERE tag_name = 'New Tag' OR tag_name = 'New Tag 2'")
    assert sorted([r[0] for r in cursor.fetchall()]) == ["New Tag", "New Tag 2"]


async def test_objects_view(cli, db_cursor, config):
    # Insert mock data
    insert_tags(tag_list, db_cursor, config, generate_tag_ids = True)
    objects = [get_test_object_link(1, ["object_data"]), get_test_object_link(2, ["object_data"]), get_test_object_link(3, ["object_data"])]
    insert_objects(objects, db_cursor, config)
    objects_tags = {1: [1, 2, 3], 2: [3, 4, 5]}
    insert_objects_tags([1], objects_tags[1], db_cursor, config)
    insert_objects_tags([2], objects_tags[2], db_cursor, config)

    # View object without tags
    object_ids = [3]
    resp = await cli.post("/objects/view", json = {"object_ids": object_ids})
    assert resp.status == 200
    data = await resp.json()
    assert type(data.get("objects")) == list
    assert len(data.get("objects")) == 1
    assert type(data["objects"][0]) == dict
    current_tag_ids = data["objects"][0].get("current_tag_ids")
    assert type(current_tag_ids) == list
    assert len(current_tag_ids) == 0

    # View objects with tags
    object_ids = [1, 2]
    resp = await cli.post("/objects/view", json = {"object_ids": object_ids})
    assert resp.status == 200
    data = await resp.json()
    for i in range(2):
        object_data = data["objects"][i]
        assert sorted(object_data["current_tag_ids"]) == sorted(objects_tags[object_data["object_id"]])


async def test_objects_delete(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    schema = config["db"]["db_schema"]

    # Insert mock values
    insert_tags(tag_list, db_cursor, config, generate_tag_ids = True)
    objects = [get_test_object_link(1, ["object_data"]), get_test_object_link(2, ["object_data"]), get_test_object_link(3, ["object_data"])]
    insert_objects(objects, db_cursor, config)
    objects_tags = {1: [1, 2, 3], 2: [3, 4, 5], 3: [1, 2, 3, 4, 5]}
    insert_objects_tags([1], objects_tags[1], db_cursor, config)
    insert_objects_tags([2], objects_tags[2], db_cursor, config)
    insert_objects_tags([3], objects_tags[3], db_cursor, config)

    # Delete 2 objects
    resp = await cli.delete("/objects/delete", json = {"object_ids": [1, 2]})
    assert resp.status == 200

    for id in [1, 2]:
        cursor.execute(f"SELECT * FROM {schema}.objects_tags WHERE object_id = {id}")
        assert not cursor.fetchone()
    cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = 3")
    assert sorted(objects_tags[3]) == sorted([r[0] for r in cursor.fetchall()])


# TODO check if setting both "remove_all_tags" and "remove_all_objects" raises an error

if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
