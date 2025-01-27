from collections import Counter
from pydantic import BaseModel, ConfigDict, Field, model_validator

from typing_extensions import Self

from backend_main.types.common import PositiveInt, Name, Datetime
from backend_main.types.domains.objects.general import ObjectsPaginationInfo, ObjectsPaginationInfoWithResult, \
    ObjectsSearchQuery
from backend_main.types.domains.objects.general import UpsertedObject
from backend_main.types.domains.objects.attributes import ObjectAttributesAndTags, AddedTags, RemovedTagIDs
from backend_main.types.domains.objects.data import ObjectIDTypeData


# /objects/bulk_upsert
class ObjectsBulkUpsertRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    objects: list[UpsertedObject] = Field(min_length=1, max_length=100)
    fully_deleted_subobject_ids: list[PositiveInt] = Field(max_length=1000)

    @model_validator(mode="after")
    def validate_unique_objects(self) -> Self:
        """ Check if object IDs are unique."""
        c = Counter((o.object_id for o in self.objects))
        non_unique_object_ids = [i for i in c if c[i] > 1]
        if len(non_unique_object_ids) > 0:
            raise ValueError(f"Received non-unique object IDs {non_unique_object_ids}.")
        return self


# NOTE: same schema is used for /objects/view route response
class ObjectsBulkUpsertResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    objects_attributes_and_tags: list[ObjectAttributesAndTags]
    objects_data: list[ObjectIDTypeData]


# /objects/update_tags
class ObjectsUpdateTagsRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    object_ids: list[PositiveInt] = Field(min_length=1, max_length=100)
    added_tags: AddedTags
    removed_tag_ids: RemovedTagIDs

    @model_validator(mode="after")
    def validate_tags_lengths(self) -> Self:
        if len(self.added_tags) == 0 and len(self.removed_tag_ids) == 0:
            raise ValueError("Either `added_tags` or `removed_tag_ids` must not be empty.")
        return self


# /objects/view
class ObjectsViewRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    object_ids: list[PositiveInt] = Field(max_length=1000)
    object_data_ids: list[PositiveInt] = Field(max_length=1000)

    @model_validator(mode="after")
    def validate_tags_lengths(self) -> Self:
        if len(self.object_ids) == 0 and len(self.object_data_ids) == 0:
            raise ValueError("Either `object_ids` or `object_data_ids` must not be empty.")
        return self


class ObjectsViewResponseBody(ObjectsBulkUpsertResponseBody):
    pass


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


class _TagUpdates(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    added_tag_ids: list[int]
    removed_tag_ids: list[int]


class ObjectsUpdateTagsResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tag_updates: _TagUpdates
    modified_at: Datetime


# /objects/view_composite_hierarchy_elements
class ObjectsViewCompositeHierarchyElementsRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    object_id: int = Field(ge=1)


# /objects/delete
class ObjectsDeleteRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    object_ids: list[PositiveInt] = Field(min_length=1, max_length=1000)
    delete_subobjects: bool


class ObjectsDeleteResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    object_ids: list[int]
