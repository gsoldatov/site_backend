from typing import Literal

from tests.data_generators.tags import get_test_tag


def get_tags_add_request_body(
    tag_id: int = 1,
    tag_name: str | None = None,
    tag_description: str | None = None,
    is_published: bool | None = None,
    added_object_ids: list[int] | None = None
):
    """ Returns /tags/add request body with default or custom attribute values. """
    tag = get_test_tag(
        tag_id=tag_id,
        tag_name=tag_name,
        tag_description=tag_description,
        is_published=is_published,
        pop_keys=["tag_id", "created_at", "modified_at"]
    )
    tag["added_object_ids"] = added_object_ids if added_object_ids is not None else []
    return {"tag": tag}


def get_tags_update_request_body(
    tag_id: int = 1,
    tag_name: str | None = None,
    tag_description: str | None = None,
    is_published: bool | None = None,
    added_object_ids: list[int] | None = None,
    removed_object_ids: list[int] | None = None
):
    """ Returns /tags/update request body with default or custom attribute values. """
    tag = get_test_tag(
        tag_id=tag_id,
        tag_name=tag_name,
        tag_description=tag_description,
        is_published=is_published,
        pop_keys=["created_at", "modified_at"]
    )
    tag["added_object_ids"] = added_object_ids if added_object_ids is not None else []
    tag["removed_object_ids"] = removed_object_ids if removed_object_ids is not None else []
    return {"tag": tag}


def get_page_tag_ids_request_body(
    page: int = 1,
    items_per_page: int = 2,
    order_by: Literal["tag_name", "modified_at"] = "tag_name",
    sort_order: Literal["asc", "desc"] = "asc",
    filter_text: str = ""
):
    """
    Returns /tags/get_page_tag_ids request body with default or custom values.
    """
    return {
        "pagination_info": {
            "page": page, 
            "items_per_page": items_per_page,
            "order_by": order_by,
            "sort_order": sort_order,
            "filter_text": filter_text
        }
    }


def get_tags_search_request_body(
    query_text: str = "tag",
    maximum_values: int = 10,
    existing_ids: list[int] | None = None
):
    """
    Returns /tags/search request body with default or custom values.
    """
    return {
        "query": {
            "query_text": query_text,
            "maximum_values": maximum_values,
            "existing_ids": existing_ids if existing_ids is not None else []
        }
    }
