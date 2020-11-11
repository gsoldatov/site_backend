tags_add_schema = {
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
                },
                "added_object_ids": {       # detailed checks are performed in objects_tags_update_schema
                    "type": "array"
                }
            }
        }
    }
}

tags_update_schema = {
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
                },

                "added_object_ids": {   # detailed checks are performed in objects_tags_update_schema
                    "type": "array"
                },
                "removed_object_ids": {    # detailed checks are performed in objects_tags_update_schema
                    "type": "array"
                }
            }
        }
    }
}

tags_view_delete_schema = {
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
        },
        
        "return_current_object_ids": {
            "type": "boolean"
        }
    }
}

tags_get_page_tag_ids_schema = {
    "type": "object",
    "required": ["pagination_info"],
    "additionalProperties": False,
    "properties": {
            "pagination_info": {
                "type": "object",
                "required": ["page", "items_per_page", "order_by", "sort_order", "filter_text"],
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
                        "enum": ["tag_name", "modified_at"]
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["asc", "desc"]
                    },
                    "filter_text": {
                        "type": "string",
                        "maxLength": 255
                    }
                }
            }
    }
}


tags_search_schema = {
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