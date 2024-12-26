from pydantic import BaseModel
from typing import Literal

from backend_main.validation.types import PositiveInt, Name, Password, Datetime
    

UserLevels = Literal["admin", "user"]

class User(BaseModel):
    """ Full user data, excluding password. """
    user_id: PositiveInt
    login: Name
    username: Name
    registered_at: Datetime
    user_level: UserLevels
    can_login: bool
    can_edit_objects: bool


class NewUser(BaseModel):
    """ New user data to be inserted into the database. """
    login: Name
    username: Name
    password: Password
    registered_at: Datetime
    user_level: UserLevels
    can_login: bool
    can_edit_objects: bool
