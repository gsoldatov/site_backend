from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from backend_main.validation.types import Name, Password
from backend_main.types.domains.users import UserLevels


class AuthRegisterRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    login: Name
    username: Name
    password: Password
    password_repeat: Password
    user_level: UserLevels | None = Field(default=None)
    can_login: bool | None = Field(default=None)
    can_edit_objects: bool | None = Field(default=None)

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError("Password is not correctly repeated.")
        return self
