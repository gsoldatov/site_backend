from pydantic import BaseModel, ConfigDict, Field

from backend_main.types.common import Name, PositiveInt
from backend_main.types.domains.tags import Tag


# /tags/add & /tags/update, common
class _TagsAddUpdateResponseTag(Tag):
    """
    /tags/add & /tags/update response tag attributes
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    added_object_ids: list[PositiveInt]
    removed_object_ids: list[PositiveInt]


class TagsAddUpdateResponseBody(BaseModel):
    """
    /tags/add & /tags/update response body
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    tag: _TagsAddUpdateResponseTag


# /tags/add
class _TagsAddRequestTag(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tag_name: Name
    tag_description: str
    is_published: bool
    added_object_ids: list[PositiveInt] = Field(max_length=100)


class TagsAddRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tag: _TagsAddRequestTag


# /tags/update
class _TagsUpdateRequestTag(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tag_id: PositiveInt
    tag_name: Name
    tag_description: str
    is_published: bool
    added_object_ids: list[PositiveInt] = Field(max_length=100)
    removed_object_ids: list[PositiveInt] = Field(max_length=100)


class TagsUpdateRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tag: _TagsUpdateRequestTag
