from backend_main.schemas.object_data import object_type_and_data_options
from backend_main.schemas.common import non_empty_list_of_ids, list_of_ids


object_types_enum = ["link", "markdown", "to_do_list"]

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
                },
                "added_tags": {         # detailed checks are performed in objects_tags_update_schema
                    "type": "array"
                }
            },
            "oneOf": object_type_and_data_options
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
                },
                "added_tags": {         # detailed checks are performed in objects_tags_update_schema
                    "type": "array"
                },
                "removed_tag_ids": {    # detailed checks are performed in objects_tags_update_schema
                    "type": "array"
                }
            }
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
        "object_ids": non_empty_list_of_ids(),          # ids to return general attributes for
        "object_data_ids": non_empty_list_of_ids()      # ids to return data for
    }
}

objects_delete_schema = {
    "type": "object",
    "required": ["object_ids"],
    "additionalProperties": False,
    "properties": {
        "object_ids": non_empty_list_of_ids()
    }
}

objects_get_page_object_ids_schema = {
    "type": "object",
    "required": ["pagination_info"],
    "additionalProperties": False,
    "properties": {
        "pagination_info": {
            "type": "object",
            "required": ["page", "items_per_page", "order_by", "sort_order", "filter_text", "object_types", "tags_filter"],
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
                },
                "tags_filter": list_of_ids()
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
                },
                "existing_ids": list_of_ids()
            }
        }
    }
}

objects_update_tags_schema = {  # Detailed property checks are performed in update_objects_tags function
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "object_ids": True,
        "added_tags": True,
        "removed_tag_ids": True
    }
}