object_types_enum = ["link"]

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
            }
        }
    }
}

objects_update_schema_link_object_data = {
    "required": ["link"],
    "additionalProperties": False,
    "properties": {
        "link": {
            "type": "string"
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

objects_get_page_object_ids_schema = {
    "type": "object",
    "required": ["pagination_info"],
    "additionalProperties": False,
    "properties": {
            "pagination_info": {
                "type": "object",
                "required": ["page", "items_per_page", "order_by", "sort_order", "filter_text", "object_types"],
                "additionalProperties": False,
                "properties": {
                    "page": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "items_per_page": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "order_by": {
                        "type": "string",
                        "enum": ["object_name", "modified_at"]
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["asc", "desc"]
                    },
                    "filter_text": {
                        "type": "string",
                        "maxLength": 255
                    },
                    "object_types": {
                        "type": "array",
                        "uniqueItems": True,
                        "items": {
                            "type": "string",
                            "enum": object_types_enum
                        }
                    }
                }
            }
    }
}

objects_search_schema = {
    "type": "object",
    "required": ["query"],
    "additionalProperties": False,
    "properties": {
        "query": {
            "type": "object",
            "required": ["query_text"],
            "additionalProperties": False,
            "properties": {
                "query_text": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 255
                },
                "maximum_values": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100
                }
            }
        }
    }
}