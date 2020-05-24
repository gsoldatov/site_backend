tag_add_schema = {
    "type": "object",
    "anyOf": [
        {"required": ["tag_id", "tag_name"]},
        {"required": ["tag_name"]}
    ],
    "additionalProperties": False,
    "properties": {
        "tag_id": {
            "type": "integer",
            "minimum": 1
        },
        "tag_name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 255
        },
        "tag_description": {
            "type": "string"
        }
    }
}

tag_update_schema = {
    "type": "object",
    "anyOf": [
        {"required": ["tag_name"]},
        {"required": ["tag_description"]}
    ],
    "additionalProperties": False,
    "properties": {
        "tag_name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 255
        },
        "tag_description": {
            "type": "string"
        }
    }
}