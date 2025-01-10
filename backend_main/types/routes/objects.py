from pydantic import BaseModel, ConfigDict, Field

from backend_main.types.common import PositiveInt


# /objects/delete
class ObjectsDeleteRequestBody(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    object_ids: list[PositiveInt] = Field(min_length=1, max_length=1000)
    delete_subobjects: bool


class ObjectsDeleteResponseBody(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    object_ids: list[int]
