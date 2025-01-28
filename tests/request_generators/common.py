from tests.data_generators.objects import get_test_object
from tests.data_generators.sessions import headers_admin_token

from tests.request_generators.objects import get_bulk_upsert_request_body, get_objects_view_request_body, \
    get_objects_delete_body, get_page_object_ids_request_body, get_objects_search_request_body, get_update_tags_request_body
from tests.request_generators.tags import get_tags_add_request_body, get_tags_update_request_body, \
    get_page_tag_ids_request_body, get_tags_search_request_body

from tests.data_sets.common import headers_logging_out_user_token

from typing import Any


class RouteHandlerInfo:
    """ Info about app route handler and a valid request body for it. """
    def __init__(
            self,
            path: str,
            method: str,
            body: dict[Any, Any],
            headers: dict[Any, Any] | None = headers_admin_token,
            uses_transaction: bool = False,
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
        self.returns_json = returns_json
        """ Route is expected to return a JSON response, if True. """


def get_route_handler_info_map(config):
    """
    Returns a mapping between app route, method and a corresponding `RouteHandlerInfo` object.

    NOTE: the list below must be updated whenever new route handlers are added to the app.
    """
    default_user_login = config.app.default_user.login.value
    default_user_password = config.app.default_user.password.value

    route_handler_info_list = [
        # /auth/...
        RouteHandlerInfo("/auth/register", "POST", {"login": "new_user", "username": "New username",
                                                    "password": "password", "password_repeat": "password"}),
        RouteHandlerInfo("/auth/login", "POST", {"login": default_user_login, "password": default_user_password}, 
                         headers=None,  # sent by anonymous
                         uses_transaction=True),
        RouteHandlerInfo("/auth/logout", "POST", {}, returns_json=False,
                         headers=headers_logging_out_user_token  # sent by another user, so that admin's token is intact
                         ),

        # /tags/...
        RouteHandlerInfo("/tags/add", "POST", get_tags_add_request_body(), uses_transaction=True),
        RouteHandlerInfo("/tags/update", "PUT", get_tags_update_request_body(tag_id=100), uses_transaction=True),
        RouteHandlerInfo("/tags/view", "POST", {"tag_ids": [100]}),
        RouteHandlerInfo("/tags/delete", "DELETE", {"tag_ids": [100]}),
        RouteHandlerInfo("/tags/get_page_tag_ids", "POST", get_page_tag_ids_request_body()),
        RouteHandlerInfo("/tags/search", "POST", get_tags_search_request_body(maximum_values=2)),
        
        # /objects/...
        RouteHandlerInfo(
            "/objects/add", "POST", {"object": get_test_object(1, pop_keys=["object_id", "created_at", "modified_at"])},
            uses_transaction=True
        ),

        RouteHandlerInfo(
            "/objects/update", "PUT", {"object": get_test_object(
                100, object_type="link", pop_keys=["created_at", "modified_at", "object_type"]
            )}, uses_transaction=True),

        RouteHandlerInfo(
            "/objects/bulk_upsert", "POST" , get_bulk_upsert_request_body(), uses_transaction=True
        ),

        RouteHandlerInfo("/objects/update_tags", "PUT", get_update_tags_request_body(
            object_ids=[101], added_tags=[101], removed_tag_ids=[]
            ), uses_transaction=True),
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
            uses_transaction=True),
        RouteHandlerInfo("/users/view", "POST", {"user_ids": [1]}),

        # /search/...
        RouteHandlerInfo("/search", "POST", {"query": {"query_text": "word", "page": 1, "items_per_page": 10}})
    ]

    return {rhi.path: {rhi.method: rhi} for rhi in route_handler_info_list}
