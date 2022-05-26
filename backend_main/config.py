import os
import json

from jsonschema import validate

from backend_main.validation.schemas.config import config_schema


def get_config(config_file = None):
    if not config_file:
        config_file = os.path.dirname(os.path.abspath(__file__)) \
            + "\config.json"
    
    config = _read_config(config_file)
    _validate_and_set_values(config)
    hide_config_values(config)
    
    return config


def _read_config(config_file):
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"File {config_file} does not exist.")

    with open(config_file, "r") as read_stream:
        return json.load(read_stream)


def _validate_and_set_values(config):
    if config:
        validate(instance=config, schema=config_schema)
        return config
    else:
        raise ValueError("No config data provided.")


def hide_config_values(config):
    """
    Replaces secret configuration values with unprintable wrappers.
    """
    # Hide default user credentials
    for attr, replacement_string in (("login", "<default_app_user_login>"), ("password", "<password>")):
        config["app"]["default_user"][attr] = HiddenValue(config["app"]["default_user"][attr], replacement_string=replacement_string)
    
    # Hide default database info
    for attr, replacement_string in (("db_init_database", "<db name>"), ("db_init_username", "<username>"), ("db_init_password", "<password>")):
        config["db"][attr] = HiddenValue(config["db"][attr], replacement_string=replacement_string)
    
    # Hide app database info
    for attr, replacement_string in (("db_database", "<db name>"), ("db_username", "<username>"), ("db_password", "<password>")):
        config["db"][attr] = HiddenValue(config["db"][attr], replacement_string=replacement_string)
    
    return config


class HiddenValue:
    """
    Protects the `value` from being printed by returning `replacement_string` instead of it.
    """
    def __init__(self, value, replacement_string = "***"):
        self.value = value
        self._replacement_string = replacement_string
    
    def __repr__(self):
        return self._replacement_string
    
    def __str__(self):
        return self._replacement_string
