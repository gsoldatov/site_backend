"""
Tests for object tagging in /objects/update_tags route as admin.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from datetime import datetime, timezone, timedelta

from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token
from tests.data_generators.tags import get_test_tag

from tests.db_operations.objects import insert_objects
from tests.db_operations.objects_tags import insert_objects_tags
from tests.db_operations.tags import insert_tags


async def test_incorrect_request_body(cli, db_cursor):
    insert_objects([get_test_object(i, owner_id=1, pop_keys=["object_data"]) for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 3)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1, 2], db_cursor)

    # Missing attributes
    for attrs in [("object_ids",), ("added_tags", "removed_tag_ids")]:
        body = {"object_ids": [1, 2], "added_tags": ["new tag"], "removed_tag_ids": [1, 2]}
        for attr in attrs: body.pop(attr)

        resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
        assert resp.status == 400
    
    # Incorrect attribute values
    incorrect_values = {
        "object_ids": [1, True, "", {}, ["a"], [-1], [0], [], [1] * 101],
        "added_tags": [1, True, "", {}, ["a" * 256], [-1], [0], [1] * 101],
        "removed_tag_ids": [1, True, "", {}, ["a"], [-1], [0], [1] * 101]
    }
    for attr, values in incorrect_values.items():
        for value in values:
            body = {"object_ids": [1, 2], "added_tags": ["new tag"], "removed_tag_ids": [1, 2]}
            body[attr] = value
            resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
            assert resp.status == 400


async def test_non_existing_object_ids(cli, db_cursor):
    insert_objects([get_test_object(i, owner_id=1, pop_keys=["object_data"]) for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 3)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1, 2], db_cursor)

    body = {"object_ids": [1, 2, 100], "added_tags": ["new tag"], "removed_tag_ids": [1, 2]}
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute("SELECT tag_id FROM tags WHERE tag_name = 'new tag'")
    assert not db_cursor.fetchone()


async def test_non_existing_added_tag_ids(cli, db_cursor):
    insert_objects([get_test_object(i, owner_id=1, pop_keys=["object_data"]) for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 3)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1, 2], db_cursor)

    body = {"object_ids": [1, 2], "added_tags": ["new tag", 100]}
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 400

    db_cursor.execute("SELECT tag_id FROM tags WHERE tag_name = 'new tag'")
    assert not db_cursor.fetchone()


async def test_non_existing_removed_tag_ids(cli, db_cursor):
    insert_objects([get_test_object(i, owner_id=1, pop_keys=["object_data"]) for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1, 2, 3, 4], db_cursor)

    body = {"object_ids": [1, 2], "removed_tag_ids": [1, 100]}
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted((r[0] for r in db_cursor.fetchall())) == [2, 3, 4]


async def test_string_added_tags(cli, db_cursor):
    insert_objects([get_test_object(i, owner_id=1, pop_keys=["object_data"]) for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(i, tag_name=f"tag {i}") for i in range(1, 6)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1, 2, 3, 4], db_cursor)

    # Add string tags & check duplicate handling
    body = {
        "object_ids": [1, 2], 
        "added_tags": [
            "New tag",                          # new tag
            "Duplicate tag", "DUPLICATE TAG",   # new tag passed twice
            "Tag 1",            # existing tag name as string
            "Tag 2", "TAG 2",   # duplicate existing tag name as string
            "Tag 3", 3          # existing tag name & its tag ID
        ]
    }
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    added_tag_ids = data["tag_updates"]["added_tag_ids"]
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 3, 6, 7]     # 4 & 5 already exist

    # Check added objects' tags
    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4, 6, 7]   # tag 5 was not added before

    # Check if new tags were added & is_published is set to true
    db_cursor.execute(f"SELECT tag_id, is_published FROM tags WHERE tag_name IN ('New tag', 'Duplicate tag')")
    assert [r[0] for r in db_cursor.fetchall()] == [6, 7]
    assert all((r[1] for r in db_cursor.fetchall()))


async def test_numeric_added_tags(cli, db_cursor):
    insert_objects([get_test_object(i, owner_id=1, pop_keys=["object_data"]) for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1, 2], db_cursor)

    # Add numeric tags and check existing tags & duplicate handling
    body = {"object_ids": [1, 2], "added_tags": [1, 2, 3, 4, 3, 4]}
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    added_tag_ids = data["tag_updates"]["added_tag_ids"]
    assert type(added_tag_ids) == list
    assert sorted(added_tag_ids) == [1, 2, 3, 4]

    # Check current objects' tags
    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2, 3, 4]


async def test_remove_tags(cli, db_cursor):
    insert_objects([get_test_object(i, owner_id=1, pop_keys=["object_data"]) for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1, 2, 3, 4], db_cursor)

    # Remove tags and check duplicate handling
    body = {"object_ids": [1, 2], "removed_tag_ids": [3, 4, 4, 4]}
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    removed_tag_ids = data["tag_updates"]["removed_tag_ids"]
    assert type(removed_tag_ids) == list
    assert sorted(removed_tag_ids) == [3, 4]

    # Check current objects' tags
    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted([r[0] for r in db_cursor.fetchall()]) == [1, 2]


async def test_add_and_remove_tags(cli, db_cursor):
    insert_objects([get_test_object(i, owner_id=1, pop_keys=["object_data"]) for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(i) for i in range(1, 5)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1, 2], db_cursor)

    # Add and remove tags simultaneously
    body = {"object_ids": [1, 2], "added_tags": [3, 4, "new tag"], "removed_tag_ids": [1, 2]}
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    assert sorted(data["tag_updates"]["added_tag_ids"]) == [3, 4, 5]
    assert sorted(data["tag_updates"]["removed_tag_ids"]) == [1, 2]

    # Check current objects' tags
    for object_id in (1, 2):
        db_cursor.execute(f"SELECT tag_id FROM objects_tags WHERE object_id = {object_id}")
        assert sorted([r[0] for r in db_cursor.fetchall()]) == [3, 4, 5]


async def test_modified_at_after_tags_addition(cli, db_cursor):
    insert_objects([
        get_test_object(i, owner_id=1, modified_at=datetime(2001, 1, 1), pop_keys=["object_data"])
    for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(1)], db_cursor, generate_ids=True)

    # Check if `modified_at` attribute of an object is updated
    body = {"object_ids": [1, 2], "added_tags": [1]}
    resp = await cli.put("/objects/update_tags", json=body, headers=headers_admin_token)
    assert resp.status == 200

    data = await resp.json()
    response_modified_at = datetime.fromisoformat(data["modified_at"])
    assert timedelta(seconds=-1) < datetime.now(tz=timezone.utc) - response_modified_at < timedelta(seconds=1)

    for object_id in (1, 2):
        db_cursor.execute(f"SELECT modified_at FROM objects WHERE object_id = {object_id}")
        assert db_cursor.fetchone()[0] == response_modified_at


async def test_modified_at_after_tags_removal(cli, db_cursor):
    insert_objects([
        get_test_object(i, owner_id=1, modified_at=datetime(2001, 1, 1), pop_keys=["object_data"])
    for i in range(1, 3)], db_cursor)
    insert_tags([get_test_tag(1)], db_cursor, generate_ids=True)
    insert_objects_tags([1, 2], [1], db_cursor)

    # Check if `modified_at` attribute of an object is updated
    body = {"object_ids": [1, 2], "removed_tag_ids": [1]}
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
