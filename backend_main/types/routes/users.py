from pydantic import BaseModel, ConfigDict, Field, AfterValidator
from typing import Annotated

from backend_main.validation.types import PositiveInt, has_unique_items
from backend_main.types.domains.users import UserFull, UserMin


_UserIDs = Annotated[
    list[PositiveInt],
    Field(min_length=1, max_length=1000),
    AfterValidator(has_unique_items)
]

class UsersViewRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    user_ids: _UserIDs
    full_view_mode: bool = Field(default=False)


class UsersViewResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    users: list[UserFull] | list[UserMin]
