"""
Tests for object tagging in /objects/... and /tags/... routes.
"""

import os
from datetime import datetime, timezone

import pytest
from psycopg2.extensions import AsIs

from fixtures.tags import insert_tags, tag_list, get_test_tag
from fixtures.objects import get_test_object, insert_objects, get_object_list
from fixtures.objects_tags import insert_objects_tags


async def test_objects_add(cli, db_cursor, config):
    schema = config["db"]["db_schema"]

    # Insert mock data
    insert_tags(tag_list, db_cursor, config, generate_tag_ids = True)

    # Incorrect object's tags
    for added_tags in ["not a list", 1, {}]:
        link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
        link["added_tags"] = added_tags
        resp = await cli.post("/objects/add", json = {"object": link})
        assert resp.status == 400

    # Add non-existing tag by tag_id (and get a 400 error)
    link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
    link["added_tags"] = [1, 100]
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 400

    # Add existing tags by tag_id and tag_name (and check duplicate tag_ids handling)
    link = get_test_object(1, pop_keys = ["object_id", "created_at", "modified_at"])
    link["added_tags"] = ["a0", 1, "b1", 2, 9, 10]
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 9, 10] # "a0", "b1", 9, 10
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 9, 10]
    
    # Add non-existing tags by tag_name (and check duplicate tag_name handling)
    link = get_test_object(2, pop_keys = ["object_id", "created_at", "modified_at"])
    link["added_tags"] = ["a0", 2, 3, 4, "New Tag", "New Tag 2", "new tag"]
    resp = await cli.post("/objects/add", json = {"object": link})
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [1, 2, 3, 4, 11, 12] # "a0", 2, 3, 4, "new tag", "new tag 2"
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 11, 12]
    db_cursor.execute(f"SELECT tag_name FROM {schema}.tags WHERE tag_name = 'New Tag' OR tag_name = 'New Tag 2'")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == ["New Tag", "New Tag 2"]


async def test_objects_update(cli, db_cursor, config):
    schema = config["db"]["db_schema"]

    # Insert mock data
    insert_tags(tag_list, db_cursor, config, generate_tag_ids = True)
    insert_objects([get_test_object(1, pop_keys = ["object_data"])], db_cursor, config)
    insert_objects_tags([1], [1, 2, 3, 4, 5], db_cursor, config)
    
    # Incorrect added_tags and removed_tag_ids
    for added_tags in ["not a list", 1, {}]:
        link = get_test_object(1, pop_keys = ["created_at", "modified_at", "object_type"])
        link["added_tags"] = added_tags
        resp = await cli.put("/objects/update", json = {"object": link})
        assert resp.status == 400
    
    for removed_tag_ids in ["not a list", 1, {}]:
        link = get_test_object(1, pop_keys = ["created_at", "modified_at", "object_type"])
        link["removed_tag_ids"] = removed_tag_ids
        resp = await cli.put("/objects/update", json = {"object": link})
        assert resp.status == 400
    
    # Add non-existing tag by tag_id (and get a 400 error)
    link = get_test_object(1, pop_keys = ["created_at", "modified_at", "object_type"])
    link["added_tags"] = [1, 100]
    resp = await cli.put("/objects/update", json = {"object": link})
    assert resp.status == 400

    # Add existing tags by tag_id and tag_name (check duplicates in request handling (added once) and retagging with the same tags (tag is reapplied))
    link = get_test_object(1, pop_keys = ["created_at", "modified_at", "object_type"])
    link["added_tags"] = ["a0", "A0", 1, "B1", "i0", "I0", 10]
    resp = await cli.put("/objects/update", json = {"object": link})
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 9, 10] # "i0", 10 were added; 1, 2 ("a0", "b1") were reapplied 
                                                  # (and should be returned for the case with partially applied tags in route with multiple objects being tagged)
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 9, 10]

    # Add non-existing tags by tag_name (and check duplicate tag_name handling) + remove existing tags
    link = get_test_object(1, pop_keys = ["created_at", "modified_at", "object_type"])
    link["added_tags"] = ["a0", 2, "New Tag", "New Tag 2", "new tag"]
    link["removed_tag_ids"] = [9, 10]
    resp = await cli.put("/objects/update", json = {"object": link})
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [1, 2, 11, 12] # 1, 2 were reapplied; "New Tag", "New Tag 2"
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 11, 12] # 9, 10 were removed; 11, 12 were added
    db_cursor.execute(f"SELECT tag_name FROM {schema}.tags WHERE tag_name = 'New Tag' OR tag_name = 'New Tag 2'")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == ["New Tag", "New Tag 2"]

    # Add tags only
    link = get_test_object(1, pop_keys = ["created_at", "modified_at", "object_type"])
    link["added_tags"] = ["a0", 2, 6, "New Tag 3"]
    resp = await cli.put("/objects/update", json = {"object": link})
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("object", {}).get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [1, 2, 6, 13] # 1, 2 were reapplied; 6 and 13 were added
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 6, 11, 12, 13] # 6 and 13 were added

    # Remove tags only
    link = get_test_object(1, pop_keys = ["created_at", "modified_at", "object_type"])
    link["removed_tag_ids"] = [11, 12, 13]
    resp = await cli.put("/objects/update", json = {"object": link})
    assert resp.status == 200
    data = await resp.json()
    removed_tag_ids = data.get("object", {}).get("tag_updates", {}).get("removed_tag_ids")
    assert sorted(removed_tag_ids) == [11, 12, 13]
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = {data['object']['object_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 6]


async def test_objects_view(cli, db_cursor, config):
    # Insert mock data
    insert_tags(tag_list, db_cursor, config, generate_tag_ids = True)
    objects = [get_test_object(1, pop_keys = ["object_data"]), get_test_object(2, pop_keys = ["object_data"]), get_test_object(3, pop_keys = ["object_data"])]
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
    schema = config["db"]["db_schema"]

    # Insert mock values
    insert_tags(tag_list, db_cursor, config, generate_tag_ids = True)
    objects = [get_test_object(1, pop_keys = ["object_data"]), get_test_object(2, pop_keys = ["object_data"]), get_test_object(3, pop_keys = ["object_data"])]
    insert_objects(objects, db_cursor, config)
    objects_tags = {1: [1, 2, 3], 2: [3, 4, 5], 3: [1, 2, 3, 4, 5]}
    insert_objects_tags([1], objects_tags[1], db_cursor, config)
    insert_objects_tags([2], objects_tags[2], db_cursor, config)
    insert_objects_tags([3], objects_tags[3], db_cursor, config)

    # Delete 2 objects
    resp = await cli.delete("/objects/delete", json = {"object_ids": [1, 2]})
    assert resp.status == 200

    for id in [1, 2]:
        db_cursor.execute(f"SELECT * FROM {schema}.objects_tags WHERE object_id = {id}")
        assert not db_cursor.fetchone()
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = 3")
    assert sorted(objects_tags[3]) == sorted([r[0] for r in db_cursor.fetchall()])


async def test_tags_add(cli, db_cursor, config):
    schema = config["db"]["db_schema"]
    
    # Insert mock data
    insert_objects(get_object_list(1, 10), db_cursor, config)
    
    # Incorrect tag's objects
    for added_object_ids in ["not a list", 1, {}]:
        tag = get_test_tag(1, pop_keys = ["tag_id", "created_at", "modified_at"])
        tag["added_object_ids"] = added_object_ids
        resp = await cli.post("/tags/add", json = {"tag": tag})
        assert resp.status == 400

    # Attempt to tag non-existing objects (and get a 404 error)
    tag = get_test_tag(1, pop_keys = ["tag_id", "created_at", "modified_at"])
    tag["added_object_ids"] = [1, 100]
    resp = await cli.post("/tags/add", json = {"tag": tag})
    assert resp.status == 400

    # Tag existing objects (and check duplicate object_ids handling)
    tag = get_test_tag(1, pop_keys = ["tag_id", "created_at", "modified_at"])
    tag["added_object_ids"] = [1, 2, 4, 6, 4, 6, 4, 6]
    resp = await cli.post("/tags/add", json = {"tag": tag})
    assert resp.status == 200
    data = await resp.json()
    added_object_ids = data.get("tag", {}).get("object_updates", {}).get("added_object_ids")
    assert sorted(added_object_ids) == [1, 2, 4, 6]
    db_cursor.execute(f"SELECT object_id FROM {schema}.objects_tags WHERE tag_id = {data['tag']['tag_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 4, 6]


async def test_tags_update(cli, db_cursor, config):
    schema = config["db"]["db_schema"]

    # Insert mock data
    insert_objects(get_object_list(1, 10), db_cursor, config)
    insert_tags([get_test_tag(1)], db_cursor, config)
    insert_objects_tags([1, 2, 3, 4, 5], [1], db_cursor, config)

    # Incorrect added_object_ids and removed_object_ids
    for added_object_ids in ["not a list", 1, {}]:
        tag = get_test_tag(1, pop_keys = ["created_at", "modified_at"])
        tag["added_object_ids"] = added_object_ids
        resp = await cli.put("/tags/update", json = {"tag": tag})
        assert resp.status == 400
    
    for removed_object_ids in ["not a list", 1, {}]:
        tag = get_test_tag(1, pop_keys = ["created_at", "modified_at"])
        tag["removed_object_ids"] = removed_object_ids
        resp = await cli.put("/tags/update", json = {"tag": tag})
        assert resp.status == 400
    
    # Attempt to tag non-existing objects (and get a 404 error)
    tag = get_test_tag(1, pop_keys = ["created_at", "modified_at"])
    tag["added_object_ids"] = [1, 100]
    resp = await cli.put("/tags/update", json = {"tag": tag})
    assert resp.status == 400

    # Tag/untag existing objects (and check duplicate object_ids handling)
    tag = get_test_tag(1, pop_keys = ["created_at", "modified_at"])
    tag["added_object_ids"] = [3, 4, 6, 7, 6, 7]
    tag["removed_object_ids"] = [1, 2]
    resp = await cli.put("/tags/update", json = {"tag": tag})
    assert resp.status == 200
    data = await resp.json()
    added_object_ids = data.get("tag", {}).get("object_updates", {}).get("added_object_ids")
    assert sorted(added_object_ids) == [3, 4, 6, 7]
    db_cursor.execute(f"SELECT object_id FROM {schema}.objects_tags WHERE tag_id = {data['tag']['tag_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [3, 4, 5, 6, 7] # 1, 2 were removed; 6, 7 were added

    # Tag objects only
    tag = get_test_tag(1, pop_keys = ["created_at", "modified_at"])
    tag["added_object_ids"] = [1, 2, 3, 1, 2]
    resp = await cli.put("/tags/update", json = {"tag": tag})
    assert resp.status == 200
    data = await resp.json()
    added_object_ids = data.get("tag", {}).get("object_updates", {}).get("added_object_ids")
    assert sorted(added_object_ids) == [1, 2, 3]
    db_cursor.execute(f"SELECT object_id FROM {schema}.objects_tags WHERE tag_id = {data['tag']['tag_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 6, 7] # 1, 2 were added

    # Untag objects only
    tag = get_test_tag(1, pop_keys = ["created_at", "modified_at"])
    tag["removed_object_ids"] = [2, 1, 1, 2]
    resp = await cli.put("/tags/update", json = {"tag": tag})
    assert resp.status == 200
    data = await resp.json()
    removed_object_ids = data.get("tag", {}).get("object_updates", {}).get("removed_object_ids")
    assert sorted(removed_object_ids) == [1, 2]
    db_cursor.execute(f"SELECT object_id FROM {schema}.objects_tags WHERE tag_id = {data['tag']['tag_id']}")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [3, 4, 5, 6, 7] # 1, 2 were removed


async def test_tags_view(cli, db_cursor, config):
    # Insert mock data
    tags = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
    insert_tags(tags, db_cursor, config)
    insert_objects(get_object_list(1, 10), db_cursor, config)
    tags_objects = {1: [1, 2, 3], 2: [3, 4, 5]}
    insert_objects_tags(tags_objects[1], [1], db_cursor, config)
    insert_objects_tags(tags_objects[2], [2], db_cursor, config)

    # View tag without tagged objects
    tag_ids = [3]
    resp = await cli.post("/tags/view", json = {"tag_ids": tag_ids, "return_current_object_ids": True})
    assert resp.status == 200
    data = await resp.json()
    assert type(data.get("tags")) == list
    assert len(data.get("tags")) == 1
    assert type(data["tags"][0]) == dict
    current_object_ids = data["tags"][0].get("current_object_ids")
    assert type(current_object_ids) == list
    assert len(current_object_ids) == 0

    # View tags with tagged objects
    tag_ids = [1, 2]
    resp = await cli.post("/tags/view", json = {"tag_ids": tag_ids, "return_current_object_ids": True})
    assert resp.status == 200
    data = await resp.json()
    for i in range(2):
        tag_data = data["tags"][i]
        assert sorted(tag_data["current_object_ids"]) == sorted(tags_objects[tag_data["tag_id"]])


async def test_tags_delete(cli, db_cursor, config):
    schema = config["db"]["db_schema"]

    # Insert mock values
    insert_objects(get_object_list(1, 10), db_cursor, config)
    tags = [get_test_tag(1), get_test_tag(2), get_test_tag(3)]
    insert_tags(tags, db_cursor, config)
    tags_objects = {1: [1, 2, 3], 2: [3, 4, 5], 3: [1, 2, 3, 4, 5]}
    insert_objects_tags(tags_objects[1], [1], db_cursor, config)
    insert_objects_tags(tags_objects[2], [2], db_cursor, config)
    insert_objects_tags(tags_objects[3], [3], db_cursor, config)

    # Delete 2 tags
    resp = await cli.delete("/tags/delete", json = {"tag_ids": [1, 2]})
    assert resp.status == 200

    for id in [1, 2]:
        db_cursor.execute(f"SELECT * FROM {schema}.objects_tags WHERE tag_id = {id}")
        assert not db_cursor.fetchone()
    db_cursor.execute(f"SELECT object_id FROM {schema}.objects_tags WHERE tag_id = 3")
    assert sorted(tags_objects[3]) == sorted([r[0] for r in db_cursor.fetchall()])


async def test_objects_update_tags(cli, db_cursor, config):
    schema = config["db"]["db_schema"]
    obj_list = get_object_list(1, 10)

    # Insert mock values
    insert_tags(tag_list, db_cursor, config, generate_tag_ids = True)
    insert_objects(obj_list, db_cursor, config)
    objects_tags = {1: [1, 2, 3], 2: [3, 4, 5]}
    insert_objects_tags([1], objects_tags[1], db_cursor, config)
    insert_objects_tags([2], objects_tags[2], db_cursor, config)


    # Incorrect attributes
    for attr in ["remove_all_tags", "tag_ids", "added_object_ids", "removed_object_ids"]:
        updates = {"object_ids": [1], "added_tags": [3, 4, 5, 6]}
        updates[attr] = [1, 2, 3]
        resp = await cli.put("/objects/update_tags", json = updates)
        assert resp.status == 400

    # Incorrect parameter values
    for attr in ["object_ids", "added_tags", "removed_tag_ids"]:
        for incorrect_value in [1, "1", {}]:
            updates = {"object_ids": [1], "added_tags": [3, 4, 5, 6]}
            updates[attr] = incorrect_value
            resp = await cli.put("/objects/update_tags", json = updates)
            assert resp.status == 400
    
    # Add non-existing tags by tag_id (and receive a 400 error)
    updates = {"object_ids": [1], "added_tags": [1, 100]}
    resp = await cli.put("/objects/update_tags", json = updates)
    assert resp.status == 400

    # Update non-existing objects (and receive a 400 error)
    updates = {"object_ids": [1, 100], "added_tags": [3, 4, 5, 6]}
    resp = await cli.put("/objects/update_tags", json = updates)
    assert resp.status == 400
    
    # Add new tags by tag_name and tag_ids (and check duplicate handling)
    updates = {"object_ids": [1], "added_tags": [4, 5, 6, "New Tag", 4, 5, "c0"]}
    resp = await cli.put("/objects/update_tags", json = updates)
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [3, 4, 5, 6, 11] # c0 = 3; 11 was added for "New Tag"
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 6, 11]
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = 2")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == sorted(objects_tags[2])
    assert data.get("tag_updates", {}).get("removed_tag_ids") == []

    # Check modified_at values for modfied and not modified objects
    # Response from server format: "2021-04-27T15:29:41.701892+00:00"
    # Cursor value format - datetime without timezone, converted to str: "2021-04-27 15:43:02.557558"
    db_cursor.execute(f"SELECT modified_at FROM {schema}.objects WHERE object_id = 1")
    db_modified_at_value = db_cursor.fetchone()[0].replace(tzinfo=timezone.utc) # add a UTC timezone for correct comparison
    assert db_modified_at_value == datetime.strptime(data["modified_at"], "%Y-%m-%dT%H:%M:%S.%f%z")

    db_cursor.execute(f"SELECT modified_at FROM {schema}.objects WHERE object_id = 2")
    assert db_cursor.fetchone()[0] == obj_list[1]["modified_at"]

    # Remove tags by tag_id
    updates = {"object_ids": [1], "removed_tag_ids": [1, 2, 3]}
    resp = await cli.put("/objects/update_tags", json = updates)
    assert resp.status == 200
    data = await resp.json()
    assert data.get("tag_updates", {}).get("added_tag_ids") == []
    removed_tag_ids = data.get("tag_updates", {}).get("removed_tag_ids")
    assert sorted(removed_tag_ids) == [1, 2, 3]
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [4, 5, 6, 11] # 1, 2, 3 were removed
    
    # Add and remove tags simultaneously
    updates = {"object_ids": [1, 2], "added_tags": [1, 2, "New Tag 2"], "removed_tag_ids": [3, 4, 5]}
    resp = await cli.put("/objects/update_tags", json = updates)
    assert resp.status == 200
    data = await resp.json()
    added_tag_ids = data.get("tag_updates", {}).get("added_tag_ids")
    assert sorted(added_tag_ids) == [1, 2, 12] # 12 was added for "New Tag 2"
    removed_tag_ids = data.get("tag_updates", {}).get("removed_tag_ids")
    assert sorted(removed_tag_ids) == [3, 4, 5]
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = 1")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 6, 11, 12] # 1, 2, 12 were added; 4, 5 were removed
    db_cursor.execute(f"SELECT tag_id FROM {schema}.objects_tags WHERE object_id = 2")
    assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 12] # 1, 2 were added; 3, 4, 5 were removed


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
