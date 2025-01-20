from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from backend_main.types.common import PositiveInt, Name
from backend_main.types.domains.objects.attributes import ObjectType


# Objects pagination
class ObjectsPaginationInfo(BaseModel):
    """
    Objects pagination info attributes, used in request.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    page: int = Field(ge=1)
    items_per_page: int = Field(ge=1)
    order_by: Literal["object_name", "modified_at", "feed_timestamp"]
    sort_order: Literal["asc", "desc"]
    filter_text: str = Field(default="", max_length=255)
    object_types: list[ObjectType] = Field(default_factory=list, max_length=4)
    tags_filter: list[PositiveInt] = Field(default_factory=list, max_length=100)
    show_only_displayed_in_feed: bool = Field(default=False)


class ObjectsPaginationInfoWithResult(ObjectsPaginationInfo):
    """
    Objects pagination info attributes and query results.
    """
    object_ids: list[int]
    total_items: int


# Objects search
class ObjectsSearchQuery(BaseModel):
    """
    Objects search query attributes.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    query_text: Name
    maximum_values: int = Field(ge=1, le=100)
    existing_ids: list[PositiveInt] = Field(max_length=100)


# Composite hierarchy
class CompositeHierarchy(BaseModel):
    """
    Object IDs present in the hierarchy of a composite object.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    composite: list[int]
    non_composite: list[int]
