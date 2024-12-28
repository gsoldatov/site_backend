from pydantic import BaseModel
from typing import Literal

from backend_main.types.common import PositiveInt, Name, Password, Datetime
    

UserLevel = Literal["admin", "user"]


class User(BaseModel):
    """ Full user data, excluding password. """
    user_id: PositiveInt
    login: Name
    username: Name
    registered_at: Datetime
    user_level: UserLevel
    can_login: bool
    can_edit_objects: bool


class NewUser(BaseModel):
    """ New user data to be inserted into the database. """
    login: Name
    username: Name
    password: Password
    registered_at: Datetime
    user_level: UserLevel
    can_login: bool
    can_edit_objects: bool


class UserFull(BaseModel):
    """ Full set of public user attributes. """
    user_id: PositiveInt
    username: Name
    registered_at: Datetime
    user_level: UserLevel
    can_login: bool
    can_edit_objects: bool


class UserMin(BaseModel):
    """ Minimal set of public user attributes. """
    user_id: PositiveInt
    username: Name
    registered_at: Datetime


class UserUpdate(BaseModel):
    """ Updated attributes of a user. """
    user_id: PositiveInt
    login: Name | None = None
    username: Name | None = None
    password: Password | None = None
    user_level: UserLevel | None = None
    can_login: bool | None = None
    can_edit_objects: bool | None = None
