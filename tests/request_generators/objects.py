from typing import Literal

from backend_main.types.domains.objects import ObjectType


def get_objects_delete_body(object_ids: list[int] | None = None, delete_subobjects: bool = False):
    """ Returns request body for /objects/delete route. """
    return { 
        "object_ids": object_ids if object_ids is not None else [1],
        "delete_subobjects": delete_subobjects
    }


def get_page_object_ids_request_body(
        page: int = 1,
        items_per_page: int = 2,
        order_by: Literal["object_name", "modified_at", "feed_timestamp"] = "object_name",
        sort_order: Literal["asc", "desc"] = "asc",
        filter_text: str | None = None,
        object_types: list[ObjectType] | None = None,
        tags_filter: list[int] | None = None,
        show_only_displayed_in_feed: bool | None = None
    ):
    """
    Returns /objects/get_page_object_ids request body with default or custom values.
    Optional attributes are omitted, unless passed explicitly.
    """
    pagination_info = {
        "page": page, 
        "items_per_page": items_per_page,
        "order_by": order_by,
        "sort_order": sort_order,
    }
    if filter_text is not None: pagination_info["filter_text"] = filter_text
    if object_types is not None: pagination_info["object_types"] = object_types
    if tags_filter is not None: pagination_info["tags_filter"] = tags_filter
    if show_only_displayed_in_feed is not None:
        pagination_info["show_only_displayed_in_feed"] = show_only_displayed_in_feed
    
    return {"pagination_info": pagination_info}


def get_objects_search_request_body(
    query_text: str = "object",
    maximum_values: int = 10,
    existing_ids: list[int] | None = None
):
    """
    Returns /objects/search request body with default or custom values.
    """
    return {
        "query": {
            "query_text": query_text,
            "maximum_values": maximum_values,
            "existing_ids": existing_ids if existing_ids is not None else []
        }
    }


def get_update_tags_request_body(
    object_ids: list[int] | None = None,
    added_tags: list[int | str] | None = None,
    removed_tag_ids: list[int] | None = None
):
    """
    Returns /objects/update_tags request body with default or custom values.
    
    Defaults: [1, 2], ["new tag"], [1, 2].
    """
    return {
        "object_ids": object_ids if object_ids is not None else [1, 2],
        "added_tags": added_tags if added_tags is not None else ["new tag"],
        "removed_tag_ids": removed_tag_ids if removed_tag_ids is not None else [1, 2]
    }
