from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from backend_main.types.common import PositiveInt, Name, Datetime


class Tag(BaseModel):
    """
    Data class containing attributes of a tag.
    """
    model_config = ConfigDict(extra="ignore", strict=True)

    tag_id: PositiveInt
    created_at: Datetime
    modified_at: Datetime
    tag_name: Name
    tag_description: str
    is_published: bool


class AddedTag(BaseModel):
    """
    Added tag properties, which are inserted into the database.
    """
    model_config = ConfigDict(extra="ignore", strict=True)

    created_at: Datetime
    modified_at: Datetime
    tag_name: Name
    tag_description: str
    is_published: bool


class TagNameToIDMap(BaseModel):
    """
    Data class, containing a mapping between tag names and IDs.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    map: dict[str, int]


class TagsPaginationInfo(BaseModel):
    """
    Tags pagination info attributes, used in request.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    page: int = Field(ge=1)
    items_per_page: int = Field(ge=1)
    order_by: Literal["tag_name", "modified_at"]
    sort_order: Literal["asc", "desc"]
    filter_text: str = Field(max_length=255)


class TagsPaginationInfoWithResult(TagsPaginationInfo):
    """
    Tags pagination info attributes and query results.
    """
    tag_ids: list[int]
    total_items: int


class TagsSearchQuery(BaseModel):
    """
    Tags search query attributes.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    query_text: Name
    maximum_values: int = Field(ge=1, le=100)
    existing_ids: list[PositiveInt] = Field(max_length=100)
