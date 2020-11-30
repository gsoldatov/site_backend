objects_tags_update_schema = {
    "type": "object",
    "oneOf": [
        # Objects' data updating options (update tags for specific objects)
        { "allOf": [
            { "anyOf": [
                { "required": ["object_ids", "added_tags"] },
                { "required": ["object_ids", "removed_tag_ids"] },
                { 
                    "required": ["object_ids", "remove_all_tags"],
                    "properties": {
                        "remove_all_tags": {
                            "const": True
                        }
                    }
                }
            ]},
            { "properties": { # tags' updating properties are not allowed
                "tag_ids": False,
                "added_object_ids": False,
                "removed_object_ids": False,
                "remove_all_objects": False
            }}
        ]},
        # Tags' data updating options (update objects for specific tags)
        { "allOf": [
            { "anyOf": [
                { "required": ["tag_ids", "added_object_ids"] },
                { "required": ["tag_ids", "removed_object_ids"] },
                { 
                    "required": ["tag_ids", "remove_all_objects"],
                    "properties": {
                        "remove_all_objects": {
                            "const": True
                        }
                    }
                }
            ]},
            { "properties": { # objects' updating properties are not allowed
                "object_ids": False,
                "added_tags": False,
                "removed_tag_ids": False,
                "remove_all_tags": False
            }}
        ]}
    ],
    "additionalProperties": False,
    "properties": {
        # Objects' data updating properties
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

        # Tags' data updating properties
        "tag_ids": {
            "type": "array",
            "minItems": 1,
            "maxItems": 1000,
            "items": {
                "type": "integer",
                "minimum": 1
            }
        },
        
        "added_object_ids": {
            "type": "array",
            "maxItems": 100,
            "items": {
                "type": "integer",
                "minimum": 1
            }
        },

        "removed_object_ids": {
            "type": "array",
            "maxItems": 100,
            "items": {
                "type": "integer",
                "minimum": 1
            }
        },

        "remove_all_objects": {
            "type": "boolean"
        }
    }
}