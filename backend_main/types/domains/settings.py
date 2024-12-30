from pydantic import BaseModel, ConfigDict, model_validator, ModelWrapValidatorHandler
from typing import Any
from typing_extensions import Self

from backend_main.types.common import PositiveInt, Name, Password, has_unique_items, HasNonNullFields
from backend_main.types.domains.users import UserFull, UserMin, UserLevel


class Setting(BaseModel):
    """
    A single setting in database the format.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    setting_name: str
    setting_value: str
    is_public: bool


class SerializedSettings(BaseModel):
    """
    Frontend settings format (listed in key-value format &
    converted to non-strings, where appropriate).
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    # Settings & their frontend types (listed as optional)
    non_admin_registration_allowed: bool | None = None

    def deserialize_setting_value(self, setting_name: str) -> str:
        """
        Returns a string representation of a setting value for provided `setting_name`.
        """
        if setting_name == "non_admin_registration_allowed":
            return "TRUE" if getattr(self, setting_name) else "FALSE"
        
        raise KeyError(f"No conversion rule defined for setting '{setting_name}'.")

    # def serialize(self) -> list[Setting]:
    #     """
    #     Converts attributes to the format, which is inserted into the database;
    #     values are also converted to strings.        
    #     """
    #     result: list[Setting] = []

    #     for name, value in self.model_fields.items():
    #         if value is not None:
    #             # Convert value to string
    #             # NOTE: add converters for new settings here
    #             if name == "non_admin_registration_allowed":
    #                 str_value = "TRUE" if value else "FALSE"
    #             else:
    #                 raise Exception(f"No conversion rule defined for setting '{name}'.")
                
    #             result.append(Setting(setting_name=name, setting_value=str_value))
        
    #     return result
