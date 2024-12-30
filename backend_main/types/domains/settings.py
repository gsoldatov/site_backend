from pydantic import BaseModel, ConfigDict
from typing import Any
from typing_extensions import Self


class Setting(BaseModel):
    """
    A single setting in database the format.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    setting_name: str
    setting_value: str
    is_public: bool

    @property
    def serialized_setting_value(self) -> Any:
        # NOTE: add serialization rules for new settings here
        if self.setting_name == "non_admin_registration_allowed":
            return bool(self.setting_value == "TRUE")
        else:
            raise KeyError(f"No serialization rule defined for setting '{self.setting_name}'.")



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
        # NOTE: add deserialization rules for new settings here
        if setting_name == "non_admin_registration_allowed":
            return "TRUE" if getattr(self, setting_name) else "FALSE"
        
        raise KeyError(f"No deserialization rule defined for setting '{setting_name}'.")
    
    @classmethod
    def from_setting_list(cls, settings_list: list[Setting]) -> Self:
        """
        Processes a list of settings with string values into a `SerializedSettings` instance.
        """
        settings_dict: dict[str, Any] = {}

        for s in settings_list:
            settings_dict[s.setting_name] = s.serialized_setting_value
        
        return cls.model_validate(settings_dict)
