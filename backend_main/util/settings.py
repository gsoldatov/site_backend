from aiohttp import web

from backend_main.util.json import error_json


def serialize_settings(settings):
    """ Accepts `settings` from /settings/update request body and returns a list of records to be stored in the corresponding database table. """
    return [{
        "setting_name": name,
        "setting_value": _SETTING_SERIALIZATION_PARAMETERS[name]["serialization_function"](settings[name]), 
        "is_public": _SETTING_SERIALIZATION_PARAMETERS[name]["is_public"]
    } for name in settings]


def deserialize_setting(name, value):
    """ Returns a deserialized setting `value` of the setting with provided `name`. """
    return _SETTING_DESERIALIZATION_FUNCTIONS[name](value)


_SETTING_DESERIALIZATION_FUNCTIONS = {
    "non_admin_registration_allowed": lambda v: v == "TRUE"
}


_SETTING_SERIALIZATION_PARAMETERS = {
    "non_admin_registration_allowed": { 
        "serialization_function": lambda v: "TRUE" if v else "FALSE",
        "is_public": True
    }
}