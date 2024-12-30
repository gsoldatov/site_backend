from pydantic import BaseModel, ConfigDict, Field, AfterValidator, model_validator
from typing import Annotated
from typing_extensions import Self

from backend_main.types.common import PositiveInt, Name, Password, has_unique_items, HasNonNullFields
from backend_main.types.domains.settings import SerializedSettings


# /settings/update
class _SettingsUpdateSettings(HasNonNullFields, SerializedSettings):
    """ Frontend-typed setting with at least one setting present. """
    pass


class SettingsUpdateRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    settings: _SettingsUpdateSettings
