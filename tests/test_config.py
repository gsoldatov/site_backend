"""
config.py tests
"""
import os, sys
from copy import deepcopy

import pytest
from jsonschema import ValidationError

sys.path.insert(0, os.path.join(sys.path[0], '..'))
from backend_main.config import _validate_and_set_values


def test_setting_groups(base_config):
    setting_groups = ["app", "cors_urls", "db"]

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


def test_app_config(base_config):
    required_app_settings = ["host", "port", "default_user", "token_lifetime"]
    required_default_user_settings = ["login", "password", "username"]

    # Check lack of required app setting
    for setting in required_app_settings:
        config = deepcopy(base_config)
        config["app"].pop(setting)
        with pytest.raises(ValidationError):
            _validate_and_set_values(config)
    
    # Check incorrect app setting values
    for k, v in [("host", ""), ("host", 0), ("port", 1024), ("port", 65536), ("default_user", 0), ("default_user", ""), 
        ("token_lifetime", 0), ("token_lifetime", 90 * 24 * 60 * 60 + 1), ("token_lifetime", "str")]:
        config = deepcopy(base_config)
        config["app"][k] = v
        with pytest.raises(ValidationError):
            _validate_and_set_values(config)
            
    
    # Check lack of required default user settings
    for setting in required_default_user_settings:
        config = deepcopy(base_config)
        config["app"]["default_user"].pop(setting)
        with pytest.raises(ValidationError):
            _validate_and_set_values(config)
        
    # Check incorrect default user setting values
    for k, v in [("login", ""), ("login", 0), ("password", "a" * 7), ("password", "a" * 73), ("password", 0),
        ("username", ""), ("username", 0)]:
        config = deepcopy(base_config)
        config["app"]["default_user"][k] = v
        with pytest.raises(ValidationError):
            _validate_and_set_values(config)


def test_cors_urls(base_config):
    # Check empty list and incorrect types
    for incorrect_cors_urls in [123, [], [123]]:
        config = deepcopy(base_config)
        config["cors_urls"] = incorrect_cors_urls
        with pytest.raises(ValidationError):
            _validate_and_set_values(config)


def test_db_config(base_config):
    required_db_settings = ["db_host", "db_port", "db_init_database", "db_init_username", 
                        "db_init_password", "db_database"]
    
    # Check lack of required db settings
    for setting in required_db_settings:
        config = deepcopy(base_config)
        config["db"].pop(setting)
        with pytest.raises(ValidationError):
            _validate_and_set_values(config)
    
    # Check incorrect setting values
    for k, v in [("db_host", ""), ("db_host", 0), ("db_port", 1024), ("db_port", 65536), ("db_port", "str"),
        ("db_init_database", ""), ("db_init_database", 0), ("db_init_username", ""), ("db_init_username", 0), 
        ("db_init_password", ""), ("db_init_password", 0), ("db_database", ""), ("db_database", 0)]:
        config = deepcopy(base_config)
        config["db"][k] = v
        with pytest.raises(ValidationError):
            _validate_and_set_values(config)


def test_correct_configs(base_config):
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
