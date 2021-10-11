from backend_main.schemas.common import name


settings_update_schema = {
    "type": "object",
    "required": ["settings"],
    "additionalProperties": False,
    "properties": {
        "settings": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "non_admin_registration_allowed": { "type": "boolean" }
            }
        }
    }
}


settings_view_schema = {
    "type": "object",
    "oneOf": [
        { "required": ["view_all"] },
        { "required": ["setting_names"] }
    ],
    "additionalProperties": False,
    "properties": {
        "view_all": { "type": "boolean", "enum": [True] },
        "setting_names": {
            "type": "array",
            "minItems": 1,
            "maxItems": 1000,
            "items": name
        }
    }
}
