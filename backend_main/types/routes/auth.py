from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from backend_main.util.exceptions import IncorrectCredentialsException

from backend_main.types.common import Name, Password, PositiveInt, Datetime
from backend_main.types.domains.users import UserLevel


class AuthRegisterRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    login: Name
    username: Name
    password: Password
    password_repeat: Password
    user_level: UserLevel | None = Field(default=None)
    can_login: bool | None = Field(default=None)
    can_edit_objects: bool | None = Field(default=None)

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError("Password is not correctly repeated.")
        return self


class AuthLoginRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    login: str # Name
    password: str # Password

    @model_validator(mode="after")
    def validate_string_credentials(self) -> Self:
        """
        Add a custom exception for invalid string login & password
        in order to raise a 401 exception instead of a 400.
        """
        if not 1 <= len(self.login) <= 255 or not 8 <= len(self.password) <= 72:
            raise IncorrectCredentialsException

        return self


class _AuthLoginResponseBodyAuth(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    access_token: str
    access_token_expiration_time: Datetime
    user_id: PositiveInt
    user_level: UserLevel


class AuthLoginResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    auth: _AuthLoginResponseBodyAuth
