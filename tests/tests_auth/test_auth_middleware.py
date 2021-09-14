from datetime import datetime, timedelta

import pytest

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.fixtures.objects import get_test_object, get_test_object_data, insert_objects, insert_links
from tests.fixtures.tags import get_test_tag, insert_tags
from tests.fixtures.users import get_test_user, insert_users, headers_admin_token, admin_token


async def test_access_token_parsing(app, cli):
    # Check incorrect access_token format for all routes
    for route in app.router.routes():
        if route.method in ("OPTIONS", "HEAD"): continue    # Don't check routes created by Aiohttp-CORS
        url = route.url_for()
        client_method = getattr(cli, route.method.lower())

        for auth_header in ("wrong format", "Bearer "):
            resp = await client_method(url, headers={"Authorization": auth_header})
            assert resp.status == 401
            data = await resp.json()
            assert data["_error"] == "Incorrect token format."
        

async def test_invalid_access_token_refusal(app, cli, db_cursor):
    # Add an expired session for admin
    expired_token = "expired token"
    expiration_time = datetime.utcnow() + timedelta(seconds=-60)
    db_cursor.execute(f"INSERT INTO sessions (user_id, access_token, expiration_time) VALUES (1, '{expired_token}', '{expiration_time}')")

    # Add another user who can't login and an active session for him
    insert_users([get_test_user(2, user_level="admin", can_login=False, pop_keys=["password_repeat"])], db_cursor)
    active_token_with_disabled_login = "active token with disabled login"
    expiration_time = datetime.utcnow() + timedelta(seconds=60)
    db_cursor.execute(f"INSERT INTO sessions (user_id, access_token, expiration_time) VALUES (2, '{active_token_with_disabled_login}', '{expiration_time}')")

    # Check incorrect access_token format for all routes, excluding /auth/logout & /auth/get_registration_status
    for route in app.router.routes():
        url = route.url_for()
        if str(url) in ["/auth/logout", "/auth/get_registration_status"]: continue
        if route.method in ("OPTIONS", "HEAD"): continue    # Don't check routes created by Aiohttp-CORS
        
        client_method = getattr(cli, route.method.lower())

        for token in ("non-existing token", expired_token, active_token_with_disabled_login):
            resp = await client_method(url, headers={"Authorization": f"Bearer {token}"})
            assert resp.status == 401
            data = await resp.json()
            assert data["_error"] == "Invalid token."


async def test_access_token_prolongation_as_admin(app, cli, db_cursor, config):
    # Insert mock data
    obj_list = [get_test_object(i, object_type="link", owner_id=1, pop_keys=["object_data"]) for i in range(100, 102)]
    l_list = [get_test_object_data(i, object_type="link") for i in range(100, 102)]
    insert_objects(obj_list, db_cursor)
    insert_links(l_list, db_cursor)

    tag_list = [get_test_tag(i) for i in range(100, 102)]
    insert_tags(tag_list, db_cursor)

    # Correct request bodies
    correct_request_bodies = {
        "/tags/add": {"POST": {"tag": get_test_tag(1, pop_keys=["tag_id", "created_at", "modified_at"])}},
        "/tags/update": {"PUT": {"tag": get_test_tag(100, pop_keys=["created_at", "modified_at"])}},
        "/tags/view": {"POST": {"tag_ids": [100]}},
        "/tags/delete": {"DELETE": {"tag_ids": [100]}},
        "/tags/get_page_tag_ids": {"POST": {"pagination_info": {"page": 1, "items_per_page": 2, "order_by": "tag_name", "sort_order": "asc", "filter_text": ""}}},
        "/tags/search": {"POST": {"query": {"query_text": "tag", "maximum_values": 2}}},
        
        "/objects/add": {"POST": {"object": get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])}},
        "/objects/update": {"PUT": {"object": get_test_object(100, object_type="link", pop_keys=["created_at", "modified_at", "object_type"])}},
        "/objects/view": {"POST": {"object_ids": [100]}},
        "/objects/delete": {"DELETE": {"object_ids": [100]}},
        "/objects/get_page_object_ids": {"POST": {
            "pagination_info": {"page": 1, "items_per_page": 2, "order_by": "object_name", "sort_order": "asc", "filter_text": "", "object_types": ["link"], "tags_filter": []}}},
        "/objects/search": {"POST": {"query": {"query_text": "object", "maximum_values": 10}}},

        "/objects/update_tags": {"PUT": {"object_ids": [101], "added_tags": [101]}}
    }

    # Check token prolongation on successful requests for all non-auth routes
    for route in app.router.routes():
        url = str(route.url_for())
        if str(url).startswith("/auth"): continue
        if route.method in ("OPTIONS", "HEAD"): continue    # Don't check routes created by Aiohttp-CORS

        # Reset access token_expiration time
        expiration_time = datetime.utcnow() + timedelta(seconds=5)
        db_cursor.execute(f"UPDATE sessions SET expiration_time = '{expiration_time}' WHERE access_token = '{admin_token}'")
        
        # Send a correct request to route
        client_method = getattr(cli, route.method.lower())
        request_body = correct_request_bodies[url][route.method]

        # Check if correct access_token_expiration_time was returned in the request field
        resp = await client_method(url, json=request_body, headers=headers_admin_token)
        assert resp.status == 200
        data = await resp.json()
        assert "auth" in data

        response_expiration_time = datetime.fromisoformat(data["auth"]["access_token_expiration_time"]).replace(tzinfo=None)
        assert timedelta(seconds=0) <= datetime.utcnow() - (response_expiration_time - timedelta(seconds=config["app"]["token_lifetime"])) <= timedelta(seconds=1)

        # Check if expiration time was updated in the database
        db_cursor.execute(f"SELECT expiration_time FROM sessions WHERE access_token = '{admin_token}'")
        assert db_cursor.fetchone()[0] == response_expiration_time


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
