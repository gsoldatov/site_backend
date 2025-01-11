from pydantic import BaseModel, ConfigDict, Field

from backend_main.types.common import PositiveInt
from backend_main.types.domains.objects import ObjectsPaginationInfo, ObjectsPaginationInfoWithResult


# /objects/delete
class ObjectsDeleteRequestBody(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    object_ids: list[PositiveInt] = Field(min_length=1, max_length=1000)
    delete_subobjects: bool


class ObjectsDeleteResponseBody(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    object_ids: list[int]


# /objects/get_page_object_ids
class ObjectsGetPageObjectIDsRequestBody(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    pagination_info: ObjectsPaginationInfo


class ObjectsGetPageObjectIDsResponseBody(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    pagination_info: ObjectsPaginationInfoWithResult
