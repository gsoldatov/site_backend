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
                    "type": "string"
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
            },
            "oneOf": [
                # link-specific data
                {
                    "properties": {
                        "object_type": {
                            "const": "link"
                        },
                        "object_data": {
                            "required": ["link"],
                        "additionalProperties": False,
                            "properties": {
                                "link": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                }
                
            ]
        }
    }
}

objects_update_schema = {
    "type": "object",
    "required": ["object"],
    "additionalProperties": False,
    "properties": {
        "object": {
            "type": "object",
            "required": ["object_id", "object_name", "object_description", "object_data"],
            "additionalProperties": False,
            "properties": {
                "object_id": {
                    "type": "integer",
                    "minimum": 1
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
            },
            "oneOf": [
                # link-specific data
                {
                    "properties": {
                        "object_type": {
                            "const": "link"
                        },
                        "object_data": {
                            "required": ["link"],
                        "additionalProperties": False,
                            "properties": {
                                "link": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                }
                
            ]
        }
    }
}

objects_view_schema = {
    "type": "object",
    "anyOf": [
        { "required": ["object_ids"] },
        { "required": ["object_data_ids"] }
    ],
    
    "additionalProperties": False,
    "properties": {
        "object_ids": {     # ids to return general attributes for
            "type": "array",
            "minItems": 1,
            "maxItems": 10000,
            "items" : {
                "type": "integer",
                "minimum": 1
            }
        },
        "object_data_ids": {    # ids to return data for
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

objects_delete_schema = {
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