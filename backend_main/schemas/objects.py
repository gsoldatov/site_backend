objects_add_schema = {
    "type": "object",
    "required": ["object"],
    "additionalProperties": False,
    "properties": {
        "object": {
            "type": "object",
            "required": ["object_type", "object_name", "object_description", "object_data"],
            "additionalProperties": False,
            "properties": {
                "object_type": {
                    "type": "string",
                    "enum": ["link", "markdown", "todo", "composite", "files"]
                },
                "object_name": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 255
                },
                "object_description": {
                    "type": "string"
                },
                "object_data": {
                    "type": "object"
                }
            }
        }
    }
}

objects_view_delete_schema = {
    "type": "object",
    "required": ["object_ids"],
    "additionalProperties": False,
    "properties": {
        "object_ids": {
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