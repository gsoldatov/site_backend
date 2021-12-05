import os
import json

from jsonschema import validate

from backend_main.validation.schemas.config import config_schema


def get_config(config_file = None):
    if not config_file:
        config_file = os.path.dirname(os.path.abspath(__file__)) \
            + "\config.json"
    
    config = _read_config(config_file)
    config = _validate_and_set_values(config)
    
    return config


def _read_config(config_file):
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"File {config_file} does not exist.")
    data = None

    with open(config_file, "r") as read_stream:
        return json.load(read_stream)


def _validate_and_set_values(config):
    if config:
        validate(instance=config, schema=config_schema)

        if config["db"].get("db_username"):
            config["db"]["create_user_required"] = True
        else:
            config["db"]["create_user_required"] = False
            config["db"]["db_username"] = config["db"]["db_init_username"]
            config["db"]["db_password"] = config["db"]["db_init_password"]
        
        return config
    else:
        raise ValueError("No config data provided.")
