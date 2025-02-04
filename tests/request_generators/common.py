from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token

from tests.request_generators.objects import get_bulk_upsert_request_body, get_bulk_upsert_object, \
    get_objects_view_request_body, get_objects_delete_body, get_page_object_ids_request_body, \
    get_objects_search_request_body, get_update_tags_request_body
from tests.request_generators.tags import get_tags_add_request_body, get_tags_update_request_body, \
    get_page_tag_ids_request_body, get_tags_search_request_body

from tests.data_sets.common import headers_logging_out_user_token

from typing import Any, Callable
from psycopg2._psycopg import cursor


def get_route_handler_info_map(config):
    """
    Returns a mapping between app route, method and a corresponding `RouteHandlerInfo` object.

    NOTE: the list below must be updated whenever new route handlers are added to the app.
    """
    default_user_login = config.app.default_user.login.value
    default_user_password = config.app.default_user.password.value
    rollback_cases = _get_rollback_cases(config)

    route_handler_info_list = [
        # /auth/...
        RouteHandlerInfo("/auth/register", "POST", {"login": "new_user", "username": "New username",
                                                    "password": "password", "password_repeat": "password"}),

        RouteHandlerInfo("/auth/login", "POST", {"login": default_user_login, "password": default_user_password},
                         headers=None,  # sent by anonymous
                         uses_transaction=True,
                         rollback_cases=rollback_cases["/auth/login"]),
        RouteHandlerInfo("/auth/logout", "POST", {}, returns_json=False,
                         headers=headers_logging_out_user_token  # sent by another user, so that admin's token is intact
                         ),

        # /tags/...
        RouteHandlerInfo("/tags/add", "POST", get_tags_add_request_body(), 
                         uses_transaction=True, rollback_cases=rollback_cases["/tags/add"]),
        RouteHandlerInfo("/tags/update", "PUT", get_tags_update_request_body(tag_id=100),
                         uses_transaction=True, rollback_cases=rollback_cases["/tags/update"]),
        RouteHandlerInfo("/tags/view", "POST", {"tag_ids": [100]}),
        RouteHandlerInfo("/tags/delete", "DELETE", {"tag_ids": [100]}),
        RouteHandlerInfo("/tags/get_page_tag_ids", "POST", get_page_tag_ids_request_body()),
        RouteHandlerInfo("/tags/search", "POST", get_tags_search_request_body(maximum_values=2)),
        
        # /objects/...
        RouteHandlerInfo(
            "/objects/add", "POST", {"object": get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])},
            uses_transaction=True, rollback_cases=rollback_cases["/objects/add"]
        ),

        RouteHandlerInfo(
            "/objects/update", "PUT", {"object": get_test_object(
                100, object_type="link", pop_keys=["created_at", "modified_at", "object_type"]
            )}, uses_transaction=True, rollback_cases=rollback_cases["/objects/update"]),

        RouteHandlerInfo(
            "/objects/bulk_upsert", "POST" , get_bulk_upsert_request_body(), uses_transaction=True,
            rollback_cases=rollback_cases["/objects/bulk_upsert"]
        ),

        RouteHandlerInfo("/objects/update_tags", "PUT", get_update_tags_request_body(
            object_ids=[101], added_tags=[101], removed_tag_ids=[]
            ), uses_transaction=True, rollback_cases=rollback_cases["/objects/update_tags"]),
        RouteHandlerInfo("/objects/view", "POST", get_objects_view_request_body(object_ids=[100], object_data_ids=[])),
        RouteHandlerInfo("/objects/get_page_object_ids", "POST", get_page_object_ids_request_body()),
        RouteHandlerInfo("/objects/search", "POST", get_objects_search_request_body()),
        RouteHandlerInfo("/objects/view_composite_hierarchy_elements", "POST", {"object_id": 99999}),
        RouteHandlerInfo("/objects/delete", "DELETE", get_objects_delete_body(object_ids=[100])),

        # /settings/...
        RouteHandlerInfo("/settings/update", "PUT", {"settings": {"non_admin_registration_allowed": False}}),
        RouteHandlerInfo("/settings/view", "POST", {"view_all": True}),

        # /users/...
        RouteHandlerInfo("/users/update", "PUT", {"user": {
            "user_id": 1, "username": "new username"}, "token_owner_password": default_user_password},
            uses_transaction=True, rollback_cases=rollback_cases["/users/update"]),
        RouteHandlerInfo("/users/view", "POST", {"user_ids": [1]}),

        # /search/...
        RouteHandlerInfo("/search", "POST", {"query": {"query_text": "word", "page": 1, "items_per_page": 10}})
    ]

    return {rhi.path: {rhi.method: rhi} for rhi in route_handler_info_list}


class RouteHandlerInfo:
    """ Info about app route handler and a valid request body for it. """
    def __init__(
            self,
            path: str,
            method: str,
            body: dict[Any, Any],
            headers: dict[Any, Any] | None = headers_admin_token,
            uses_transaction: bool = False,
            rollback_cases: list["RollbackCase"] | None = None,
            returns_json: bool = True
        ):
        self.path = path
        self.method = method
        self.body = body
        """ Valid request body for the route. """
        self.headers = headers
        """ Headers sent in a valid request. """

        self.uses_transaction = uses_transaction
        """ Route handler is expected to start a transaction, if True. """
        self.rollback_cases = rollback_cases
        """ A list of cases, which ensure response status and db state after sending specific request bodies. """
        self.returns_json = returns_json
        """ Route is expected to return a JSON response, if True. """


class RollbackCase:
    """
    A single set of request body with an expected response status and a function, which checks the state of a database.
    """
    def __init__(
            self,
            body: dict[str, Any],
            expected_status: int,
            db_checks: list[Callable[[cursor], None]]
        ):
        self.body = body
        self.expected_status = expected_status
        self.db_checks = db_checks


def _get_rollback_cases(config):
    """ Returns a dict with lists of `RollbackCase` objects for transaction using handlers. """
    default_user_login = config.app.default_user.login.value
    default_user_password = config.app.default_user.password.value
    existing_tag_name = get_tags_add_request_body(tag_id=100)["tag"]["tag_name"]
    unmodified_tag_name = get_tags_add_request_body(tag_id=101)["tag"]["tag_name"]

    return {
        "/auth/login": [
            ## Incorrect password submitted
            RollbackCase(body={"login": default_user_login, "password": "incorrect password"},
                expected_status=401, db_checks=[_user_id_has_x_sessions(1, 1)]  # a single admin session exists by default
            ),

            ## User, who can't log in
            RollbackCase(body={"login": "login", "password": "password"},
                expected_status=403, db_checks=[_user_id_has_x_sessions(100, 0)]
            )
        ],

        "/tags/add": [
            # Existing tag name
            RollbackCase(body=get_tags_add_request_body(tag_name=existing_tag_name),
                expected_status=400, db_checks=[_tag_id_does_not_exist(1)]
            )
        ],

        "/tags/update": [
            # Non-existing tag
            RollbackCase(body=get_tags_update_request_body(tag_id=999),
                expected_status=404, db_checks=[_tag_id_does_not_exist(999)]
            ),
            # Existing tag name
            RollbackCase(body=get_tags_update_request_body(tag_id=101, tag_name=existing_tag_name),
                expected_status=400, db_checks=[_tag_id_has_name(101, unmodified_tag_name)]
            )
        ],

        "/objects/add": [
            # Non-existing owner
            RollbackCase(body={
                    **get_test_object(1, owner_id=999, pop_keys=["object_id", "created_at", "modified_at"]),
                    "added_tags": ["new tag"]
                },
                expected_status=400, db_checks=[
                    _object_id_does_not_exist(1),
                    _tag_name_does_not_exist("new tag")
                ]
            ),
            # Non-existing added tag ID
            RollbackCase(body={
                    **get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"]),
                    "added_tags": ["new tag", 999]
                },
                expected_status=400, db_checks=[
                    _object_id_does_not_exist(1),
                    _tag_name_does_not_exist("new tag")
                ]
            ),
        ],

        "/objects/update": [
            # Non-existing owner
            RollbackCase(body={
                    **get_test_object(100, object_name="updated name", owner_id=999, pop_keys=["object_type", "created_at", "modified_at"]),
                    "added_tags": ["new tag"]
                },
                expected_status=400, db_checks=[
                    _object_name_does_not_exist("updated name"),
                    _tag_name_does_not_exist("new tag")
                ]
            ),
            # Non-existing added tag ID
            RollbackCase(body={
                    **get_test_object(100, object_name="updated name", pop_keys=["object_type", "created_at", "modified_at"]),
                    "added_tags": ["new tag", 999]
                },
                expected_status=400, db_checks=[
                    _object_name_does_not_exist("updated name"),
                    _tag_name_does_not_exist("new tag")
                ]
            ),
            # Non-existing object ID
            RollbackCase(body={
                    **get_test_object(999, object_name="updated name", pop_keys=["object_type", "created_at", "modified_at"]),
                    "added_tags": ["new tag"]
                },
                expected_status=400, db_checks=[
                    _object_name_does_not_exist("updated name"),
                    _tag_name_does_not_exist("new tag")
                ]
            ),
            # Changed object type
            RollbackCase(body={
                    **get_test_object(100, object_name="updated name", object_type="composite", owner_id=999, pop_keys=["object_type", "created_at", "modified_at"]),
                    "added_tags": ["new tag"]
                },
                expected_status=400, db_checks=[
                    _object_name_does_not_exist("updated name"),
                    _tag_name_does_not_exist("new tag")
                ]
            ),
        ],

        "/objects/bulk_upsert": [
            # Non-existing owner
            RollbackCase(body=get_bulk_upsert_request_body(objects=[
                get_bulk_upsert_object(),
                get_bulk_upsert_object(object_id=100, object_name="updated_name", added_tags=["new tag"]),
                get_bulk_upsert_object(object_id=101, owner_id=999)
            ]),
                expected_status=400, db_checks=[
                    _object_id_does_not_exist(1),
                    _object_name_does_not_exist("updated name"),
                    _tag_name_does_not_exist("new tag")
                ]
            ),
            # Non-existing added tag
            RollbackCase(body=get_bulk_upsert_request_body(objects=[
                get_bulk_upsert_object(),
                get_bulk_upsert_object(object_id=100, object_name="updated_name", added_tags=["new tag"]),
                get_bulk_upsert_object(object_id=101, added_tags=[999])
            ]),
                expected_status=400, db_checks=[
                    _object_id_does_not_exist(1),
                    _object_name_does_not_exist("updated name"),
                    _tag_name_does_not_exist("new tag")
                ]
            ),
            # Non-existing updated object ID
            RollbackCase(body=get_bulk_upsert_request_body(objects=[
                get_bulk_upsert_object(),
                get_bulk_upsert_object(object_id=100, object_name="updated_name", added_tags=["new tag"]),
                get_bulk_upsert_object(object_id=999)
            ]),
                expected_status=400, db_checks=[
                    _object_id_does_not_exist(1),
                    _object_name_does_not_exist("updated name"),
                    _tag_name_does_not_exist("new tag")
                ]
            ),
            # Changed object type
            RollbackCase(body=get_bulk_upsert_request_body(objects=[
                get_bulk_upsert_object(),
                get_bulk_upsert_object(object_id=100, object_name="updated_name", added_tags=["new tag"]),
                get_bulk_upsert_object(object_id=101, object_type="composite")
            ]),
                expected_status=400, db_checks=[
                    _object_id_does_not_exist(1),
                    _object_name_does_not_exist("updated name"),
                    _tag_name_does_not_exist("new tag")
                ]
            ),
        ],

        "/objects/update_tags": [
            # Object IDs don't exist
            RollbackCase(body=get_update_tags_request_body(
                    object_ids=[100, 999], added_tags=["new tag", 100]
                ),
                expected_status=400, db_checks=[
                    _tag_name_does_not_exist("new tag"),
                    _object_tag_pair_does_not_exist(100, 100)
                ]
            ),
            # Tag IDs don't exist
            RollbackCase(body=get_update_tags_request_body(
                    object_ids=[100], added_tags=["new tag", 100, 999]
                ),
                expected_status=400, db_checks=[
                    _tag_name_does_not_exist("new tag"),
                    _object_tag_pair_does_not_exist(100, 100)
                ]
            )
        ],

        "/users/update": [
            # User ID does not exist
            RollbackCase(body={
                "user": {
                    "user_id": 999, 
                    "username": "new username"
                }, 
                "token_owner_password": default_user_password
            }, expected_status=404, db_checks=[_username_does_not_exist("new username")])
        ]
    }


# Transaction rollback test cases' db checking functions
def _user_id_has_x_sessions(user_id: int, expected_session_count: int):
    def inner(db_cursor: cursor):
        """ Check if an expected amount of user sessions exists. """
        db_cursor.execute(f"SELECT COUNT(*) FROM sessions WHERE user_id = {user_id}")
        assert db_cursor.fetchone()[0] == expected_session_count
    return inner


def _username_does_not_exist(username: str):
    def inner(db_cursor: cursor):
        """ Check if a username does not exist. """
        db_cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
        assert not db_cursor.fetchone()
    return inner


def _tag_id_does_not_exist(tag_id: int):
    def inner(db_cursor: cursor):
        """ Check if a `tag_id` does not exist. """
        db_cursor.execute(f"SELECT * FROM tags WHERE tag_id = {tag_id}")
        assert not db_cursor.fetchone()
    return inner


def _tag_id_has_name(tag_id: int, expected_tag_name: str):
    def inner(db_cursor: cursor):
        """ Check if a `tag_id` has expected name. """
        db_cursor.execute(f"SELECT tag_name FROM tags WHERE tag_id = {tag_id}")
        assert db_cursor.fetchone()[0] == expected_tag_name
    return inner


def _tag_name_does_not_exist(tag_name: str):
    def inner(db_cursor: cursor):
        """ Check if a `tag_name` does not exist. """
        db_cursor.execute(f"SELECT tag_name FROM tags WHERE lower(tag_name) = '{tag_name.lower()}'")
        assert not db_cursor.fetchone()
    return inner


def _object_id_does_not_exist(object_id: int):
    def inner(db_cursor: cursor):
        """ Check if an `object_id` does not exist. """
        db_cursor.execute(f"SELECT * FROM objects WHERE object_id = {object_id}")
        assert not db_cursor.fetchone()
    return inner


def _object_name_does_not_exist(object_name: str):
    def inner(db_cursor: cursor):
        """ Check if an `object_name` does not exist. """
        db_cursor.execute(f"SELECT * FROM objects WHERE object_name = '{object_name}'")
        assert not db_cursor.fetchone()
    return inner


def _object_tag_pair_does_not_exist(object_id: int, tag_id: int):
    def inner(db_cursor: cursor):
        """ Check `object_id` is not tagged with `tag_id`. """
        db_cursor.execute(f"SELECT * FROM objects_tags WHERE object_id = {object_id} AND tag_id = {tag_id}")
        assert not db_cursor.fetchone()
    return inner