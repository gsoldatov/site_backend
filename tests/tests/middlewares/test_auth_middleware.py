from datetime import datetime, timezone, timedelta

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from tests.data_generators.sessions import admin_token
from tests.data_generators.users import get_test_user

from tests.data_sets.common import insert_data_for_requests_to_all_routes

from tests.db_operations.users import insert_users

from tests.request_generators.common import get_route_handler_info_map


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
    insert_data_for_requests_to_all_routes(db_cursor)

    # Check token prolongation on successful requests for all non-auth routes
    route_handler_info_map = get_route_handler_info_map(config)

    for route in app.router.routes():
        url = str(route.url_for())
        if str(url).startswith("/auth"): continue
        if route.method in ("OPTIONS", "HEAD"): continue    # Don't check routes created by Aiohttp-CORS

        # Reset access token_expiration time
        expiration_time = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
        db_cursor.execute(f"UPDATE sessions SET expiration_time = '{expiration_time}' WHERE access_token = '{admin_token}'")
        
        # Send a correct request to route
        client_method = getattr(cli, route.method.lower())
        route_handler_info = route_handler_info_map[url][route.method]

        # Check if correct access_token_expiration_time was returned in the request field
        resp = await client_method(url, json=route_handler_info.body, headers=route_handler_info.headers)
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
