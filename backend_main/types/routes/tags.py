from pydantic import BaseModel, ConfigDict, Field

from backend_main.types.common import Name, PositiveInt
from backend_main.types.domains.tags import Tag


# /tags/add & /tags/update, common
class _ResponseTag(Tag):
    """
    /tags/add & /tags/update response tag attributes
    """
    # strict=False is required for casting ISO-formatted strings to datetime
    model_config = ConfigDict(extra="forbid", strict=False)

    added_object_ids: list[PositiveInt]
    removed_object_ids: list[PositiveInt]


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


class TagsAddResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tag: _ResponseTag
