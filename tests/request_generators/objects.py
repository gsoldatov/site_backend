from tests.data_generators.objects import get_test_object

from typing import Literal, Any
from datetime import datetime
from backend_main.types.domains.objects.attributes import ObjectType


def get_bulk_upsert_request_body(
        objects: list[dict[str, Any]] | None = None,
        fully_deleted_subobject_ids: list[int] | None = None
    ):
    """
    Returns /objects/bulk_upsert request body with default or custom values.

    Defaults:
    - `objects` => a single new link with object ID = 0;
    - `fully_deleted_subobject_ids` => empty list;
    """
    return {
        "objects": objects if objects is not None else [get_bulk_upsert_object()],
        "fully_deleted_subobject_ids": fully_deleted_subobject_ids if fully_deleted_subobject_ids is not None else []
    }


def get_bulk_upsert_object(
        object_id: int = 0,
        object_type: ObjectType = "link",
        object_name: str | None = None,
        object_description: str | None = None,
        is_published: bool | None = None,
        display_in_feed: bool | None = None,
        feed_timestamp: datetime | None = None,
        show_description: bool | None = None,
        owner_id: int | None = None,
        added_tags: list[int | str] | None = None,
        removed_tag_ids: list[int] | None = None,
        object_data: dict[str, Any] | None = None
    ):
    """
    Generates a sing upserted object for /objects/bulk_upsert request body
    with default of custom attributes, tags & data.
    """
    result = {
        **get_test_object(
            object_id=object_id,
            object_type=object_type,
            object_name=object_name,
            object_description=object_description,
            is_published=is_published,
            display_in_feed=display_in_feed,
            feed_timestamp=feed_timestamp,
            show_description=show_description,
            owner_id=owner_id or 1,     # owner_id is required for this route            
            object_data=object_data,
            pop_keys=["created_at", "modified_at"]
        ),
        "added_tags": added_tags if added_tags is not None else [],
        "removed_tag_ids": removed_tag_ids if removed_tag_ids is not None else []
    }

    # Remove `deleted_subobjects` from composite object data
    result["object_data"].pop("deleted_subobjects", None)
    
    return result


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


def get_objects_view_request_body(
    object_ids: list[int] | None = None,
    object_data_ids: list[int] | None = None
):
    """
    Returns /objects/view request body with default or custom values.
    
    Defaults: [1], [1].
    """
    return {
        "object_ids": object_ids if object_ids is not None else [1],
        "object_data_ids": object_data_ids if object_data_ids is not None else [1]
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


def get_objects_delete_body(object_ids: list[int] | None = None, delete_subobjects: bool = False):
    """ Returns request body for /objects/delete route. """
    return { 
        "object_ids": object_ids if object_ids is not None else [1],
        "delete_subobjects": delete_subobjects
    }
