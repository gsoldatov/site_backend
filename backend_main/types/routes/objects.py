from pydantic import BaseModel, ConfigDict, Field, model_validator

from typing_extensions import Self

from backend_main.types.common import PositiveInt, Name, Datetime
from backend_main.types.domains.objects import ObjectsPaginationInfo, ObjectsPaginationInfoWithResult, \
    ObjectsSearchQuery


# /objects/delete
class ObjectsDeleteRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    object_ids: list[PositiveInt] = Field(min_length=1, max_length=1000)
    delete_subobjects: bool


class ObjectsDeleteResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    object_ids: list[int]


# /objects/get_page_object_ids
class ObjectsGetPageObjectIDsRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    pagination_info: ObjectsPaginationInfo


class ObjectsGetPageObjectIDsResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    pagination_info: ObjectsPaginationInfoWithResult


# /objects/search
class ObjectsSearchRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    query: ObjectsSearchQuery


class ObjectsSearchResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    object_ids: list[int]


# /objects/update_tags
class ObjectsUpdateTagsRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    object_ids: list[PositiveInt] = Field(min_length=1, max_length=100)
    added_tags: list[PositiveInt | Name] = Field(max_length=100)
    removed_tag_ids: list[PositiveInt] = Field(max_length=100)

    @model_validator(mode="after")
    def validate_tags_lengths(self) -> Self:
        if len(self.added_tags) == 0 and len(self.removed_tag_ids) == 0:
            raise ValueError("At least one added or removed tag is required.")
        return self


class _TagUpdates(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    added_tag_ids: list[int]
    removed_tag_ids: list[int]


class ObjectsUpdateTagsResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tag_updates: _TagUpdates
    modified_at: Datetime