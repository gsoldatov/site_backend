from datetime import datetime, timezone, timedelta

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from tests.data_generators.objects import get_test_object, get_test_object_data
from tests.data_generators.searchables import get_test_searchable
from tests.data_generators.sessions import headers_admin_token, admin_token
from tests.data_generators.tags import get_test_tag
from tests.data_generators.users import get_test_user

from tests.db_operations.objects import insert_objects, insert_links
from tests.db_operations.searchables import insert_searchables
from tests.db_operations.tags import insert_tags
from tests.db_operations.users import insert_users

from tests.request_generators.objects import get_objects_delete_body, get_page_object_ids_request_body
from tests.request_generators.tags import get_tags_add_request_body, get_tags_update_request_body, \
    get_page_tag_ids_request_body, get_tags_search_request_body


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
    expiration_time = datetime.now(tz=timezone.utc) + timedelta(seconds=-60)
    db_cursor.execute(f"INSERT INTO sessions (user_id, access_token, expiration_time) VALUES (1, '{expired_token}', '{expiration_time}')")

    # Add another user who can't login and an active session for him
    insert_users([get_test_user(2, user_level="admin", can_login=False, pop_keys=["password_repeat"])], db_cursor)
    active_token_with_disabled_login = "active token with disabled login"
    expiration_time = datetime.now(tz=timezone.utc) + timedelta(seconds=60)
    db_cursor.execute(f"INSERT INTO sessions (user_id, access_token, expiration_time) VALUES (2, '{active_token_with_disabled_login}', '{expiration_time}')")

    # Check incorrect access_token format for all routes, excluding /auth/logout & /settings/view
    for route in app.router.routes():
        url = route.url_for()
        if str(url) in ["/auth/logout", "/settings/view"]: continue
        if route.method in ("OPTIONS", "HEAD"): continue    # Don't check routes created by Aiohttp-CORS
        
        client_method = getattr(cli, route.method.lower())

        for token in ("non-existing token", expired_token, active_token_with_disabled_login):
            resp = await client_method(url, headers={"Authorization": f"Bearer {token}"})
            assert resp.status == 401
            data = await resp.json()
            assert data["_error"] == "Invalid token."


async def test_access_token_prolongation(app, cli, db_cursor, config):
    # Insert mock data
    obj_list = [get_test_object(i, object_type="link", owner_id=1, pop_keys=["object_data"]) for i in range(100, 102)]
    obj_list.append(get_test_object(99999, object_type="composite", owner_id=1, pop_keys=["object_data"]))
    l_list = [get_test_object_data(i, object_type="link") for i in range(100, 102)]
    insert_objects(obj_list, db_cursor)
    insert_links(l_list, db_cursor)

    tag_list = [get_test_tag(i) for i in range(100, 102)]
    insert_tags(tag_list, db_cursor)

    insert_searchables([get_test_searchable(object_id=101, text_a="word")], db_cursor)

    # Correct request bodies
    # NOTE: correct request body for new non-auth route handlers must be included in the dict below
    correct_request_bodies = {
        "/tags/add": {"POST": get_tags_add_request_body()},
        "/tags/update": {"PUT": get_tags_update_request_body(tag_id=100)},
        "/tags/view": {"POST": {"tag_ids": [100]}},
        "/tags/delete": {"DELETE": {"tag_ids": [100]}},
        "/tags/get_page_tag_ids": {"POST": get_page_tag_ids_request_body()},
        "/tags/search": {"POST": get_tags_search_request_body(maximum_values=2)},
        
        "/objects/add": {"POST": {"object": get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])}},
        "/objects/update": {"PUT": {"object": get_test_object(100, object_type="link", pop_keys=["created_at", "modified_at", "object_type"])}},
        "/objects/view": {"POST": {"object_ids": [100]}},
        "/objects/delete": {"DELETE": get_objects_delete_body(object_ids=[100])},
        "/objects/get_page_object_ids": {"POST": get_page_object_ids_request_body()},
        "/objects/search": {"POST": {"query": {"query_text": "object", "maximum_values": 10}}},
        "/objects/update_tags": {"PUT": {"object_ids": [101], "added_tags": [101]}},
        "/objects/view_composite_hierarchy_elements": {"POST": {"object_id": 99999}},

        "/settings/update": {"PUT": {"settings": {"non_admin_registration_allowed": False}}},
        "/settings/view": {"POST": {"view_all": True}},

        "/users/update": {"PUT": {"user": {"user_id": 1, "username": "new username"}, "token_owner_password": config.app.default_user.password.value}},
        "/users/view": {"POST": {"user_ids": [1]}},

        "/search": {"POST": {"query": {"query_text": "word", "page": 1, "items_per_page": 10}}}
    }

    # Check token prolongation on successful requests for all non-auth routes
    for route in app.router.routes():
        url = str(route.url_for())
        if str(url).startswith("/auth"): continue
        if route.method in ("OPTIONS", "HEAD"): continue    # Don't check routes created by Aiohttp-CORS

        # Reset access token_expiration time
        expiration_time = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
        db_cursor.execute(f"UPDATE sessions SET expiration_time = '{expiration_time}' WHERE access_token = '{admin_token}'")
        
        # Send a correct request to route
        client_method = getattr(cli, route.method.lower())
        request_body = correct_request_bodies[url][route.method]

        # Check if correct access_token_expiration_time was returned in the request field
        resp = await client_method(url, json=request_body, headers=headers_admin_token)
        assert resp.status == 200, f"Received a non 200 reponse code for route '{url}' and method '{route.method}'"
        data = await resp.json()
        assert "auth" in data

        response_expiration_time = datetime.fromisoformat(data["auth"]["access_token_expiration_time"])
        assert timedelta(seconds=0) <= datetime.now(tz=timezone.utc) - \
            (response_expiration_time - timedelta(seconds=config.app.token_lifetime)) <= timedelta(seconds=1)

        # Check if expiration time was updated in the database
        db_cursor.execute(f"SELECT expiration_time FROM sessions WHERE access_token = '{admin_token}'")
        assert db_cursor.fetchone()[0] == response_expiration_time


if __name__ == "__main__":
    run_pytest_tests(__file__)
