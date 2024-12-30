from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from backend_main.types.common import Name, AnyOf, OneOf
from backend_main.types.domains.settings import SerializedSettings


# /settings/update
class _SettingsUpdateSettings(AnyOf, SerializedSettings):
    """ Frontend-typed setting with at least one setting present. """
    pass


class SettingsUpdateRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    settings: _SettingsUpdateSettings


# /settings/view
class SettingsViewRequestBody(OneOf, BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    view_all: Literal[True] | None = None
    setting_names: list[Name] | None = Field(default=None, min_length=1, max_length=1000)


class SettingsViewResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    
    settings: SerializedSettings
