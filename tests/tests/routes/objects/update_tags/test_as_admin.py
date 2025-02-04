"""
Tests for object tagging in /objects/update_tags route as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from datetime import datetime, timezone, timedelta

from tests.data_generators.sessions import headers_admin_token
from tests.data_sets.objects import insert_objects_update_tags_test_data
from tests.request_generators.objects import get_update_tags_request_body


async def test_incorrect_request_body(cli, db_cursor):
    insert_objects_update_tags_test_data(db_cursor)

    # Invalid JSON
    resp = await cli.put("/objects/update_tags", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Missing attributes
    for attr in ("object_ids", "added_tags", "removed_tag_ids"):
        body = get_update_tags_request_body()
        body.pop(attr)
        resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute values
    incorrect_values = {
        "object_ids": [None, 1, True, "", {}, ["a"], [-1], [0], [], [1] * 101],
        "added_tags": [None, 1, True, "", {}, ["a" * 256], [-1], [0], [1] * 101],
        "removed_tag_ids": [None, 1, True, "", {}, ["a"], [-1], [0], [1] * 101]
    }
    for attr, values in incorrect_values.items():
        for value in values:
            body = get_update_tags_request_body()
            body[attr] = value
            resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
            assert resp.status == 400
    
    # Both tag lists are empty
    body = get_update_tags_request_body(added_tags=[], removed_tag_ids=[])
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 400


async def test_non_existing_object_ids(cli, db_cursor):
    insert_objects_update_tags_test_data(db_cursor)

    body = get_update_tags_request_body(object_ids=[1, 2, 100])
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute("SELECT tag_id FROM tags WHERE tag_name = 'new tag'")
    assert not db_cursor.fetchone()


async def test_non_existing_added_tag_ids(cli, db_cursor):
    insert_objects_update_tags_test_data(db_cursor)

    body = get_update_tags_request_body(added_tags=["new tag", 6, 100])
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute("SELECT tag_id FROM tags WHERE tag_name = 'new tag'")
    assert not db_cursor.fetchone()

    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted((r[0] for r in db_cursor.fetchall())) == [1, 2, 3, 4, 5]


async def test_non_existing_removed_tag_ids(cli, db_cursor):
    insert_objects_update_tags_test_data(db_cursor)

    body = get_update_tags_request_body(added_tags=[], removed_tag_ids=[1, 2, 100])
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted((r[0] for r in db_cursor.fetchall())) == [3, 4, 5]


async def test_string_added_tags(cli, db_cursor):
    insert_objects_update_tags_test_data(db_cursor)

    # Add string tags & check duplicate handling
    added_tags = [
        "New tag",                          # new tag
        "Duplicate tag", "DUPLICATE TAG",   # new tag passed twice
        "Tag name 1",                       # existing tag name as string
        "Tag name 2", "TAG NAME 2",         # duplicate existing tag name as string
        "Tag name 3", 3                     # existing tag name & its tag ID
    ]
    body = get_update_tags_request_body(added_tags=added_tags, removed_tag_ids=[])
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    added_tag_ids = data["tag_updates"]["added_tag_ids"]
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 3, 11, 12]     # 4 & 5 already exist

    # Check added objects' tags
    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 5, 11, 12]

    # Check if new tags were added & is_published is set to true
    db_cursor.execute(f"SELECT tag_id, is_published FROM tags WHERE tag_name IN ('New tag', 'Duplicate tag')")
    assert [r[0] for r in db_cursor.fetchall()] == [11, 12]
    assert all((r[1] for r in db_cursor.fetchall()))


async def test_numeric_added_tags(cli, db_cursor):
    insert_objects_update_tags_test_data(db_cursor)

    # Add numeric tags and check existing tags & duplicate handling
    body = get_update_tags_request_body(added_tags=[1, 2, 6, 7, 6, 7], removed_tag_ids=[])
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    added_tag_ids = data["tag_updates"]["added_tag_ids"]
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 6, 7]

    # Check current objects' tags
    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted([r[0] for r in db_cursor.fetchall()]) == [i for i in range(1, 8)]


async def test_remove_tags(cli, db_cursor):
    insert_objects_update_tags_test_data(db_cursor)

    # Remove tags and check duplicate handling
    body = get_update_tags_request_body(added_tags=[], removed_tag_ids=[4, 5, 5, 5])
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    removed_tag_ids = data["tag_updates"]["removed_tag_ids"]
    assert type(removed_tag_ids) == list
    assert sorted(removed_tag_ids) == [4, 5]

    # Check current objects' tags
    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3]


async def test_add_and_remove_tags(cli, db_cursor):
    insert_objects_update_tags_test_data(db_cursor)

    # Add and remove tags simultaneously
    body = get_update_tags_request_body(added_tags=[6, 7, "new tag"], removed_tag_ids=[1, 2])
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    assert sorted(data["tag_updates"]["added_tag_ids"]) == [6, 7, 11]
    assert sorted(data["tag_updates"]["removed_tag_ids"]) == [1, 2]

    # Check current objects' tags
    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted([r[0] for r in db_cursor.fetchall()]) == [3, 4, 5, 6, 7, 11]


async def test_modified_at_after_tags_addition(cli, db_cursor):
    insert_objects_update_tags_test_data(db_cursor)

    # Check if `modified_at` attribute of an object is updated
    body = get_update_tags_request_body(added_tags=[6], removed_tag_ids=[])
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    response_modified_at = datetime.fromisoformat(data["modified_at"])
    assert timedelta(seconds=-1) < datetime.now(tz=timezone.utc) - response_modified_at < timedelta(seconds=1)

    for object_id in (1, 2):
        db_cursor.execute(f"SELECT modified_at FROM objects WHERE object_id = {object_id}")
        assert db_cursor.fetchone()[0] == response_modified_at


async def test_modified_at_after_tags_removal(cli, db_cursor):
    insert_objects_update_tags_test_data(db_cursor)

    # Check if `modified_at` attribute of an object is updated
    body = get_update_tags_request_body(added_tags=[], removed_tag_ids=[1])
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    response_modified_at = datetime.fromisoformat(data["modified_at"])
    assert timedelta(seconds=-1) < datetime.now(tz=timezone.utc) - response_modified_at < timedelta(seconds=1)

    for object_id in (1, 2):
        db_cursor.execute(f"SELECT modified_at FROM objects WHERE object_id = {object_id}")
        assert db_cursor.fetchone()[0] == response_modified_at


if __name__ == "__main__":
    run_pytest_tests(__file__)
