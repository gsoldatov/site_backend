from pathlib import Path
import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator

from backend_main.validation.types import Port, NonEmptyString, HiddenString


class _DefaultUser(BaseModel):
    model_config = ConfigDict(strict=True)

    login: HiddenString
    password: HiddenString
    username: str = Field(min_length=1, max_length=255)

    @field_validator("login", mode="plain")
    @classmethod
    def login_to_hidden_value(cls, value: Any) -> HiddenString:
        """ Validate `login` attribute & convert it to `HiddenValue`. """
        return HiddenString(value, "<default_app_user_login>", 1, 255)
    
    @field_validator("password", mode="plain")
    @classmethod
    def password_to_hidden_value(cls, value: Any) -> HiddenString:
        """ Validate `password` attribute & convert it to `HiddenValue`. """
        return HiddenString(value, "<password>", 8, 72)


class _AppConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    host: NonEmptyString
    port: Port
    use_forwarded: bool
    debug: bool
    default_user: _DefaultUser
    token_lifetime: int = Field(ge=1, le=90 * 24 * 60 * 60)
    composite_hierarchy_max_depth: int = Field(ge=1, le=10)


class _DBConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    db_host: NonEmptyString
    db_port: Port
    db_init_database: HiddenString
    db_init_username: HiddenString
    db_init_password: HiddenString
    
    db_database: HiddenString
    db_password: HiddenString
    db_username: HiddenString

    @field_validator("db_init_database", mode="plain")
    @classmethod
    def db_init_database_to_hidden_value(cls, value: Any) -> HiddenString:
        """ Validate `db_init_database` & convert it to `HiddenValue` instances. """
        return HiddenString(value, "<db_name>", 1)
    
    @field_validator("db_init_username", mode="plain")
    @classmethod
    def db_init_username_to_hidden_value(cls, value: Any) -> HiddenString:
        """ Validate `db_init_username` & convert it to `HiddenValue` instances. """
        return HiddenString(value, "<username>", 1)
    
    @field_validator("db_init_password", mode="plain")
    @classmethod
    def db_init_password_to_hidden_value(cls, value: Any) -> HiddenString:
        """ Validate `db_init_password` & convert it to `HiddenValue` instances. """
        return HiddenString(value, "<password>", 1)
    

    @field_validator("db_database", mode="plain")
    @classmethod
    def db_database_to_hidden_value(cls, value: Any) -> HiddenString:
        """ Validate `db_database` & convert it to `HiddenValue` instances. """
        return HiddenString(value, "<db_name>", 1)
    
    @field_validator("db_username", mode="plain")
    @classmethod
    def db_username_to_hidden_value(cls, value: Any) -> HiddenString:
        """ Validate `db_username` & convert it to `HiddenValue` instances. """
        return HiddenString(value, "<username>", 1)
    
    @field_validator("db_password", mode="plain")
    @classmethod
    def db_password_to_hidden_value(cls, value: Any) -> HiddenString:
        """ Validate `db_password` & convert it to `HiddenValue` instances. """
        return HiddenString(value, "<password>", 1)


class _AuxillaryConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    enable_searchables_updates: bool


_AppLoggingModes = Literal["file", "stdout", "off"]


class _LoggingConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    folder: str
    file_separator: str
    file_separator_replacement: str
    
    app_event_log_mode: _AppLoggingModes
    app_event_log_file_mode_interval: int = Field(ge=1)
    
    app_access_log_mode: _AppLoggingModes
    app_access_log_file_mode_interval: int = Field(ge=1)
    
    db_mode: _AppLoggingModes
    scheduled_mode: _AppLoggingModes


class Config(BaseModel):
    model_config = ConfigDict(strict=True)

    app: _AppConfig
    cors_urls: list[Annotated[str, Field(min_length=1)]] = Field(min_length=1)
    db: _DBConfig
    auxillary: _AuxillaryConfig
    logging: _LoggingConfig


def get_config(config_file: str | None = None) -> Config:
    # Set default config path
    path = get_config_file_path(config_file)

    # Read & parse config JSON
    if not path.is_file:
        raise FileNotFoundError(f"File {path} does not exist.")
    
    with open(path, "r") as read_stream:
        config_json = json.load(read_stream)
    
    # Get a validated config
    config = Config(**config_json)
    return config


def get_config_file_path(config_file: str | None = None) -> Path:
    """
    Returns a `Path` object for the provided `config_file`
    or a default config path (`backend_main/config.json`).
    """
    return Path(config_file) if config_file else Path(__file__).parent / "config.json"
