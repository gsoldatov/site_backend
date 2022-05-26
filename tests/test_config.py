"""
config.py tests
"""
import os, sys
from copy import deepcopy

import pytest
from jsonschema import ValidationError

sys.path.insert(0, os.path.join(sys.path[0], '..'))
from backend_main.config import _validate_and_set_values


def test_top_level(base_config):
    top_level_keys = ["app", "cors_urls", "db", "auxillary"]

    # Check if all top-level setting names are present
    assert sorted(top_level_keys) == sorted(base_config.keys()), "Expected and received top-level config setting names do not match."

    # Check empty config
    with pytest.raises(ValueError):
        _validate_and_set_values({})
    
    # Check lack of setting groups
    for k in top_level_keys:
        config = deepcopy(base_config)
        config.pop(k)
        _assert_validation_exception(config, f"Validation unexpectedly passed with missing top-level setting '{k}'")


def test_app_config(base_config):
    # Incorrect settings for `app` and `default_user` config parts
    incorrect_app_setting_values = {
        "host": ("", 0, True),
        "port": (1024, 65536, "str", True),
        "debug": (1, "str"),
        "default_user": (1, "str", True),
        "token_lifetime": (0, 90 * 24 * 60 * 60 + 1, "str", True),
        "composite_hierarchy_max_depth": (0, 11, "str", True)
    }

    incorrect_default_user_values = {
        "login": ("", 1, True),
        "password": ("a" * 7, "a" * 73, 1, True),
        "username": ("", 1, True)
    }

    # Check if expected and received app setting names match
    assert sorted(incorrect_app_setting_values.keys()) == sorted(base_config["app"].keys()), "Expected and received app setting names do not match."

    # Check lack of required app settings
    for k in incorrect_app_setting_values:
        config = deepcopy(base_config)
        config["app"].pop(k)
        _assert_validation_exception(config, f"Validation unexpectedly passed with missing app setting '{k}'")
    
    # Check incorrect app setting values
    for k in incorrect_app_setting_values:
        for v in incorrect_app_setting_values[k]:
            config = deepcopy(base_config)
            config["app"][k] = v
            _assert_validation_exception(config, f"Validation unexpectedly passed with incorrect app setting '{k}' value '{v}'")
    
    # Check if expected and received default user setting names match
    assert sorted(incorrect_default_user_values.keys()) == sorted(base_config["app"]["default_user"].keys()), "Expected and received default user setting names do not match."

    # Check lack of required default user settings
    for setting in incorrect_default_user_values:
        config = deepcopy(base_config)
        config["app"]["default_user"].pop(setting)
        _assert_validation_exception(config, f"Validation unexpectedly passed with missing default user setting '{k}'")
    
    # Check incorrect default user setting values
    for k in incorrect_default_user_values:
        for v in incorrect_default_user_values[k]:
            config = deepcopy(base_config)
            config["app"]["default_user"][k] = v
            _assert_validation_exception(config, f"Validation unexpectedly passed with incorrect default user setting '{k}' value '{v}'")


def test_cors_urls(base_config):
    # Check empty list and incorrect URLs
    for incorrect_cors_urls in ["", True, 123, [], [123], ["correct", ""]]:
        config = deepcopy(base_config)
        config["cors_urls"] = incorrect_cors_urls
        _assert_validation_exception(config, f"Validation unexpectedly passed with CORS URL value(-s) '{incorrect_cors_urls}'")


def test_db_config(base_config):
    # Incorrect settings for `db` config part
    incorrect_db_config_values = {
        "db_host": ("", 1, True),
        "db_port": (1024, 65536, "str", True),
        "db_init_database": ("", 1, True),
        "db_init_username": ("", 1, True),
        "db_init_password": ("", 1, True),
        "db_database": ("", 1, True),
        "db_username": ("", 1, True),
        "db_password": ("", 1, True)
    }

    # Check if expected and received db setting names match
    assert sorted(incorrect_db_config_values.keys()) == sorted(base_config["db"].keys()), "Expected and received db setting names do not match."
    
    # Check lack of required db settings
    for k in incorrect_db_config_values:
        config = deepcopy(base_config)
        config["db"].pop(k)
        _assert_validation_exception(config, f"Validation unexpectedly passed with missing db setting '{k}'")
    
    # Check incorrect setting values
    for k in incorrect_db_config_values:
        for v in incorrect_db_config_values[k]:
            config = deepcopy(base_config)
            config["db"][k] = v
            _assert_validation_exception(config, f"Validation unexpectedly passed with incorrect db setting '{k}' value '{v}'")


def test_auxillary_config(base_config):
    # Incorrect settings for `auxillary` config part
    incorrect_auxillary_config_values = {
        "enable_searchables_updates": ("str", 1)
    }

    # Check if expected and received auxillary setting names match
    assert sorted(incorrect_auxillary_config_values.keys()) == sorted(base_config["auxillary"].keys()), "Expected and received auxillary setting names do not match."
    
    # Check lack of required auxillary settings
    for k in incorrect_auxillary_config_values:
        config = deepcopy(base_config)
        config["auxillary"].pop(k)
        _assert_validation_exception(config, f"Validation unexpectedly passed with missing auxillary setting '{k}'")
    
    # Check incorrect setting values
    for k in incorrect_auxillary_config_values:
        for v in incorrect_auxillary_config_values[k]:
            config = deepcopy(base_config)
            config["auxillary"][k] = v
            _assert_validation_exception(config, f"Validation unexpectedly passed with incorrect auxillary setting '{k}' value '{v}'")


def test_correct_config(base_config):
    _validate_and_set_values(base_config)


def _assert_validation_exception(config, msg):
    try:
        _validate_and_set_values(config)
        pytest.fail(msg)
    except ValidationError:
        pass


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
