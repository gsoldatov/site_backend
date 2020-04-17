"""
routes/tags.py tests
"""
from copy import deepcopy
import os
from psycopg2.extensions import AsIs
from datetime import datetime

from fixtures_app import *
from fixtures_tags import *


async def test_add(cli, db_cursor, config):
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


async def test_update(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    table = config["db"]["db_schema"] + ".tags"
    created_at = datetime.utcnow()

    # Insert mock value
    cursor.execute("INSERT INTO %s VALUES (1, %s, %s, %s), (2, %s, %s, %s)",
                (AsIs(table), 
                created_at, test_tag["tag_name"], test_tag["tag_description"],
                created_at, test_tag2["tag_name"], test_tag2["tag_description"])
                )
    
    # Check required elements
    tag = {}
    resp = await cli.put("/tags/update/1", json = tag)
    assert resp.status == 400

    # Unallowed elements (tag_id is sent as a part of URL)
    tag = deepcopy(test_tag)
    resp = await cli.put("/tags/update/1", json = tag)
    assert resp.status == 400

    # Incorrect values
    for k, v in incorrect_tag_values:
        if k != "tag_id":
            tag = deepcopy(test_tag)
            tag[k] = v
            tag.pop("tag_id", None)
            resp = await cli.put("/tags/update/1", json = tag)
            assert resp.status == 400
    
    # Non-existing tag_id
    tag = deepcopy(test_tag3)
    tag.pop("tag_id")
    resp = await cli.put("/tags/update/asd", json = tag)
    assert resp.status == 404

    resp = await cli.put("/tags/update/999999", json = tag)
    print(tag) #####
    print(await resp.json()) #######
    assert resp.status == 404

    # Already existing tag_name
    tag = deepcopy(test_tag2)
    tag.pop("tag_id")
    resp = await cli.put("/tags/update/1", json = tag)
    assert resp.status == 400

    # Correct update
    tag = deepcopy(test_tag3)
    tag.pop("tag_id")
    resp = await cli.put("/tags/update/1", json = tag)
    assert resp.status == 200
    cursor.execute(f"SELECT tag_name FROM {table} WHERE tag_id = 1")
    assert cursor.fetchone() == (tag["tag_name"],)


async def test_delete(cli, db_cursor, config):
    cursor = db_cursor(apply_migrations = True)
    table = config["db"]["db_schema"] + ".tags"
    created_at = datetime.utcnow()

    # Insert mock value
    cursor.execute("INSERT INTO %s VALUES (1, %s, %s, %s), (2, %s, %s, %s)",
                (AsIs(table), 
                created_at, test_tag["tag_name"], test_tag["tag_description"],
                created_at, test_tag2["tag_name"], test_tag2["tag_description"])
                )
    
    # Non-existing tag_id
    resp = await cli.delete("/tags/delete/asd")
    assert resp.status == 404

    resp = await cli.delete("/tags/delete/999999")
    assert resp.status == 404

    # Correct delete
    resp = await cli.delete("/tags/delete/1")
    assert resp.status == 200
    cursor.execute(f"SELECT tag_id FROM {table}")
    assert cursor.fetchone() == (2,)
    assert not cursor.fetchone()
    


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
