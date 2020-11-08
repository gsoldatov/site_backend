objects_tags_update_schema = {
    "type": "object",
    "anyOf": [
        { "required": ["object_ids", "added_tags"] },
        { "required": ["object_ids", "removed_tag_ids"] },
        { 
            "required": ["object_ids", "remove_all_tags"],
            "properties": {
                "remove_all_tags": {
                    "const": True
                },
                "remove_all_objects": {
                    "not": {}
                }
            }
        },
        { 
            "required": ["object_ids", "remove_all_objects"],
            "properties": {
                "remove_all_objects": {
                    "const": True
                },
                "remove_all_tags": {
                    "not": {}
                }
            }
        }
    ],
    "additionalProperties": False,
    "properties": {
        "object_ids": {
            "type": "array",
            "minItems": 1,
            "maxItems": 1000,
            "items": {
                "type": "integer",
                "minimum": 1
            }
        },

        "added_tags": {
            "type": "array",
            "maxItems": 100,
            "items": {
                "oneOf": [
                    {
                        "type": "integer",
                        "minimum": 1
                    },
                    {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 255
                    }
                ]
            }
        },

        "removed_tag_ids": {
            "type": "array",
            "maxItems": 100,
            "items": {
                "type": "integer",
                "minimum": 1
            }
        },

        "remove_all_tags": {
            "type": "boolean"
        },

        "remove_all_objects": {
            "type": "boolean"
        }
    }
}