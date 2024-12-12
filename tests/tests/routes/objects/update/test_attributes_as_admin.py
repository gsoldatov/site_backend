import pytest
from datetime import datetime

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.objects import get_test_object
from tests.fixtures.data_generators.sessions import headers_admin_token
from tests.fixtures.data_generators.users import get_test_user

from tests.fixtures.data_sets.objects import insert_data_for_update_tests

from tests.fixtures.db_operations.users import insert_users


async def test_update_with_duplicate_names(cli, db_cursor):
    # Insert mock values
    insert_data_for_update_tests(db_cursor)

    # Duplicate object_name
    obj = get_test_object(2, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200

    # Lowercase duplicate object_name
    obj = get_test_object(2, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    obj["object_name"] = obj["object_name"].upper()
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200


async def test_correct_update(cli, db_cursor):
    # Insert mock values
    insert_data_for_update_tests(db_cursor)

    # Correct update (general attributes)
    obj = get_test_object(3, is_published=True, show_description=True, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200
    db_cursor.execute(f"SELECT object_name, is_published, display_in_feed, feed_timestamp, show_description FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone() == (obj["object_name"], obj["is_published"], obj["display_in_feed"], datetime.fromisoformat(obj["feed_timestamp"]), obj["show_description"])


@pytest.mark.parametrize("owner_id", [1, 2])    # set the same and another owner_id
async def test_correct_update_with_set_owner_id(cli, db_cursor, owner_id):
    # Insert mock values
    insert_data_for_update_tests(db_cursor)
    insert_users([get_test_user(2, pop_keys=["password_repeat"])], db_cursor)

    # Correct update with set owner_id
    updated_name = "updated name"
    obj = get_test_object(3, owner_id=owner_id, object_name=updated_name, pop_keys=["created_at", "modified_at", "object_type"])
    obj["object_id"] = 1
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200
    resp_object = (await resp.json())["object"]
    assert datetime.fromisoformat(obj["feed_timestamp"]) == datetime.fromisoformat(resp_object["feed_timestamp"])
    db_cursor.execute(f"SELECT object_name, owner_id FROM objects WHERE object_id = 1")
    assert db_cursor.fetchone() == (updated_name, owner_id)

    # Update object again (check empty feed timestamp case)
    obj["feed_timestamp"] = ""
    resp = await cli.put("/objects/update", json={"object": obj}, headers=headers_admin_token)
    assert resp.status == 200
    assert (await resp.json())["object"]["feed_timestamp"] == ""


if __name__ == "__main__":
    run_pytest_tests(__file__)
