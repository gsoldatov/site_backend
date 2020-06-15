tag_add_schema = {
    "type": "object",
    "required": ["tag"],
    "additionalProperties": False,
    "properties": {
        "tag": {
            "type": "object",
            "required": ["tag_name", "tag_description"],
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
    }
}

tag_update_schema = {
    "type": "object",
    "required": ["tag"],
    "additionalProperties": False,
    "properties": {
        "tag": {
            "type": "object",
            "required": ["tag_id", "tag_name", "tag_description"],
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
    }
}

tag_view_delete_schema = {
    "type": "object",
    "required": ["tag_ids"],
    "additionalProperties": False,
    "properties": {
        "tag_ids": {
            "type": "array",
            "minItems": 1,
            "maxItems": 10000,
            "items" : {
                "type": "integer",
                "minimum": 1
            }
        }
    }
}