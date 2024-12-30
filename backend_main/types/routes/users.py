from pydantic import BaseModel, ConfigDict, Field, AfterValidator, model_validator
from typing import Annotated
from typing_extensions import Self

from backend_main.types.common import PositiveInt, Name, Password, has_unique_items, AnyOf
from backend_main.types.domains.users import UserFull, UserMin, UserLevel


# /users/update
class _UsersUpdateAnyOf(AnyOf):
    """ At least one field from the list must be non-null. """
    __any_of_fields__ = ("login", "username", "password", "user_level", "can_login", "can_edit_objects")


class _UsersUpdateData(_UsersUpdateAnyOf, BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    user_id: PositiveInt
    login: Name | None = None
    username: Name | None = None
    password: Password | None = None
    password_repeat: Password | None = None
    user_level: UserLevel | None = None
    can_login: bool | None = None
    can_edit_objects: bool | None = None

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError("Password is not correctly repeated.")
        return self
    

class UsersUpdateRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    
    user: _UsersUpdateData
    token_owner_password: Password


# /users/view
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
