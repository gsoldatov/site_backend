"""
Connection middleware and transaction management tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from tests.data_sets.common import insert_data_for_successful_requests
from tests.request_generators.common import get_route_handler_info_map


async def test_transaction_start(cli_with_start_transaction_stub, config, db_cursor):
    # Insert mock data
    insert_data_for_successful_requests(db_cursor)

    # Check if transactions are started in the expected route handlers
    route_handler_info_map = get_route_handler_info_map(config)

    for route in cli_with_start_transaction_stub.app.router.routes():
        if route.method in ("OPTIONS", "HEAD"): continue    # Don't check routes created by Aiohttp-CORS

        url = str(route.url_for())
        route_handler_info = route_handler_info_map[url][route.method]
        
        # Send a correct request to route
        client_method = getattr(cli_with_start_transaction_stub, route.method.lower())

        # Check if correct access_token_expiration_time was returned in the request field
        resp = await client_method(url, json=route_handler_info.body, headers=route_handler_info.headers)
        data = await resp.json() if route_handler_info.returns_json else {}
        assert resp.status == 200, f"Received a non 200 reponse code for route '{url}' and method '{route.method}'"

        if route_handler_info.uses_transaction:
            assert "sent_by_start_transaction_stub" in data, f"Route '{url}' did not start a start a transaction."
            assert data["caller_filename"].find("backend_main/routes/") > -1, f"Route '{url}' did not start a transaction in its handler."
        else:
            assert "sent_by_start_transaction_stub" not in data, f"Route '{url}' unexpectedly started a transaction."


if __name__ == "__main__":
    run_pytest_tests(__file__)
