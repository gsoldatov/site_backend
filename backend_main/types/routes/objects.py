from collections import Counter
from itertools import chain
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
        self._ensure_unique_object_ids()
        self._ensure_new_subobjects_have_objects()
        self._ensure_shared_tags_limits()
        self._validate_fully_deleted_subobject_ids()
        return self
    
    def _ensure_unique_object_ids(self) -> None:
        """ Check if object IDs are unique."""
        c = Counter((o.object_id for o in self.objects))
        non_unique_object_ids = [i for i in c if c[i] > 1]
        if len(non_unique_object_ids) > 0:
            raise ValueError(f"Received non-unique object IDs {non_unique_object_ids}.")
    
    def _ensure_new_subobjects_have_objects(self) -> None:
        """ Check if every new subobject (id <= 0) is passed as an object as well. """
        new_subobject_ids = set(
            so.subobject_id for so in
                chain(*(o.object_data.subobjects for o in self.objects if o.object_type == "composite"))
            if so.subobject_id <= 0
        )
        new_object_ids = set(o.object_id for o in self.objects if o.object_id <= 0)
        subobject_ids_without_objects = new_subobject_ids.difference(new_object_ids)
        if len(subobject_ids_without_objects) > 0:
            raise ValueError(f"Composite subobjects {subobject_ids_without_objects} must be passed as separate objects.")
    
    def _ensure_shared_tags_limits(self) -> None:
        ao_max, roi_max = 1000, 1000    # Shared limits for tag arrays
        if sum(len(o.added_tags) for o in self.objects) > ao_max:
            raise ValueError(f"Added tags can contain a maximum of {ao_max} for all objects combined.")
        if sum(len(o.removed_tag_ids) for o in self.objects) > roi_max:
            raise ValueError(f"Removed tag IDs can contain a maximum of {roi_max} for all objects combined.")

    def _validate_fully_deleted_subobject_ids(self) -> None:
        # Ensure fully deleted subobjects are not passed as objects
        fdso = set(self.fully_deleted_subobject_ids)
        object_ids = set(o.object_id for o in self.objects)
        if len(fd_object_ids := fdso.intersection(object_ids)) > 0:
            raise ValueError(f"Upserted objects {fd_object_ids} cannot be marked as fully deleted.")
        
        # Ensure fully deleted subobjects are not passed as subobjects of composite objects
        subobject_ids = set(
            so.subobject_id 
            for o in self.objects if o.object_type == "composite"
            for so in o.object_data.subobjects
        )
        if len(fd_subobject_ids := fdso.intersection(subobject_ids)) > 0:
            raise ValueError(f"Composite subobjects {fd_subobject_ids} cannot be marked as fully deleted.")


class ObjectsBulkUpsertResponseBody(BaseModel):
    """ NOTE: this schema partially matches /objects/view response. """
    model_config = ConfigDict(extra="forbid", strict=True)

    objects_attributes_and_tags: list[ObjectAttributesAndTags]
    objects_data: list[ObjectIDTypeData]
    new_object_ids_map: dict[int, int]


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


class ObjectsViewResponseBody(BaseModel):
    """ NOTE: this schema partially matches /objects/bulk_upsert response. """
    model_config = ConfigDict(extra="forbid", strict=True)

    objects_attributes_and_tags: list[ObjectAttributesAndTags]
    objects_data: list[ObjectIDTypeData]


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
