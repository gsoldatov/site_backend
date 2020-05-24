"""
config.py tests
"""
import os, sys
from copy import deepcopy

import pytest
from jsonschema import ValidationError

sys.path.insert(0, os.path.join(sys.path[0], '..'))

from backend_main.config import _validate_and_set_values
from fixtures_app import base_config


setting_groups = ["db"]
required_db_settings = ["db_host", "db_port", "db_init_database", "db_init_username", 
                        "db_init_password", "db_database", "db_schema"]



def test_setting_groups(base_config):
     # Check empty config
    with pytest.raises(ValueError):
        _validate_and_set_values({})
    
    # Check lack of setting groups
    if len(setting_groups) > 1:
        for group in setting_groups:
            config = deepcopy(base_config)
            config.pop(group)
            with pytest.raises(ValidationError):
                _validate_and_set_values(config)
    


def test_db_config(base_config):
    # Check lack of required db settings
    for setting in required_db_settings:
        config = deepcopy(base_config)
        config["db"].pop(setting)
        with pytest.raises(ValidationError):
            _validate_and_set_values(config)
    
    # Check incorrect setting values
    for setting in required_db_settings:
        config = deepcopy(base_config)
        config["db"][setting] = "" if setting != "db_port" else 0
        with pytest.raises(ValidationError):
            _validate_and_set_values(config)
    
    # Check correct settings without db_username and db_password
    config = deepcopy(base_config)
    config["db"].pop("db_username")
    config["db"].pop("db_password")
    result =  _validate_and_set_values(config)
    assert "db_username" in result["db"]
    assert result["db"]["db_username"] == result["db"]["db_init_username"]
    assert "db_password" in result["db"]
    assert result["db"]["db_password"] == result["db"]["db_init_password"]
    assert "create_user_required" in result["db"]
    assert not result["db"]["create_user_required"]

    # Check correct settings with db_username and db_password
    config = deepcopy(base_config)
    result =  _validate_and_set_values(config)
    assert "db_username" in result["db"]
    assert result["db"]["db_username"] == config["db"]["db_username"]
    assert "db_password" in result["db"]
    assert result["db"]["db_password"] == config["db"]["db_password"]
    assert "create_user_required" in result["db"]
    assert result["db"]["create_user_required"]


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
