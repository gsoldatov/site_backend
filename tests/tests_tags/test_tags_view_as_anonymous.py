if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.util import ensure_equal_collection_elements

from tests.fixtures.data_sets.tags import tag_list
from tests.fixtures.db_operations.tags import insert_tags


async def test_view_existing_tags(cli, db_cursor):
    # Insert data
    insert_tags(tag_list, db_cursor)

    # Correct request
    tag_ids = [tag["tag_id"] for tag in tag_list]
    resp = await cli.post("/tags/view", json={"tag_ids": tag_ids})
    assert resp.status == 200
    data = await resp.json()
    assert "tags" in data

    # Check if only published tags are returned
    expected_ids = [tag["tag_id"] for tag in tag_list if tag["is_published"]]
    assert len(expected_ids) < len(tag_ids) # ensure there are non-published tags in the fixture
    ensure_equal_collection_elements(expected_ids, [data["tags"][x]["tag_id"] for x in range(len(data["tags"]))], 
        "Tags view, correct request")
        
    for field in ("tag_id", "tag_name", "tag_description", "created_at", "modified_at", "is_published"):
        assert field in data["tags"][0]


if __name__ == "__main__":
    run_pytest_tests(__file__)
