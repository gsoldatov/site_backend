"""
routes/tags.py tests
"""
from copy import deepcopy
import os

from fixtures_app import *
from fixtures_tags import *


async def test_add_tag(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)

    # Check required elements
    tag = deepcopy(test_tag)
    tag.pop("tag_id")
    tag.pop("tag_name")
    resp = await cli.post("/tags/add", json = tag)
    assert resp.status == 400

    # Unallowed elements
    tag = deepcopy(test_tag)
    tag["unallowed"] = "unallowed"
    resp = await cli.post("/tags/add", json = tag)
    assert resp.status == 400

    # Incorrect values
    for k, v in incorrect_tag_values:
        tag = deepcopy(test_tag)
        tag[k] = v
        resp = await cli.post("/tags/add", json = tag)
        assert resp.status == 400

    # Write a correct value with a tag_id
    resp = await cli.post("/tags/add", json = test_tag)
    assert resp.status == 200
    resp_json = await resp.json()
    assert test_tag["tag_id"] == resp_json["tag_id"]
    assert test_tag["tag_name"] == resp_json["tag_name"]
    assert test_tag["tag_description"] == resp_json["tag_description"]
    assert "created_at" in resp_json

    schema = config["db"]["db_schema"]
    cursor.execute(f"SELECT tag_name FROM {schema}.tags WHERE tag_id = 1")
    assert cursor.fetchone() == (test_tag["tag_name"],)

    # Write a correct value without a tag_id
    tag = deepcopy(test_tag2)
    tag.pop("tag_id")
    resp = await cli.post("/tags/add", json = tag)
    assert resp.status == 200
    cursor.execute(f"SELECT tag_name FROM {schema}.tags WHERE tag_id = 2")
    assert cursor.fetchone() == (tag["tag_name"],)

    # Add an existing tag_name
    resp = await cli.post("/tags/add", json = test_tag)
    assert resp.status == 400


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
