from backend_main.validation.schemas.common import non_empty_list_of_ids, list_of_ids, object_id, name, description, object_types_enum
from backend_main.validation.schemas.object_data import object_type_and_data_options
from backend_main.validation.schemas.objects_tags import added_tags, removed_tag_ids


objects_add_schema = {
    "type": "object",
    "required": ["object"],
    "additionalProperties": False,
    "properties": {
        "object": {
            "type": "object",
            "oneOf": [{
                "required": ["object_type", "object_name", "object_description", "is_published", "display_in_feed", "feed_timestamp", "show_description", "object_data"],
                "additionalProperties": False,
                "properties": {
                    "object_type": { "const": object_type },
                    "object_name": name,
                    "object_description": description,
                    "is_published": {"type": "boolean"},
                    "display_in_feed": {"type": "boolean"},
                    "feed_timestamp": {"type": "string"},
                    "show_description": {"type": "boolean"},
                    "owner_id": object_id,
                    "object_data": object_type_and_data_options[object_type],
                    "added_tags": added_tags
                } 
            } for object_type in object_type_and_data_options]
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
            "required": ["object_id", "object_name", "object_description", "is_published", "display_in_feed", "feed_timestamp", "show_description", "object_data"],
            "additionalProperties": False,
            "properties": {
                "object_id": object_id,
                "object_name": name,
                "object_description": description,
                "is_published": {"type": "boolean"},
                "display_in_feed": {"type": "boolean"},
                "feed_timestamp": {"type": "string"},
                "show_description": {"type": "boolean"},
                "owner_id": object_id,
                "object_data": {
                    "type": "object"
                },
                "added_tags": added_tags,
                "removed_tag_ids": removed_tag_ids
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
        "object_ids": non_empty_list_of_ids(),
        "delete_subobjects": { "type": "boolean" }
    }
}

objects_get_page_object_ids_schema = {
    "type": "object",
    "required": ["pagination_info"],
    "additionalProperties": False,
    "properties": {
        "pagination_info": {
            "type": "object",
            "required": ["page", "items_per_page", "order_by", "sort_order"],
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
                    "enum": ["object_name", "modified_at", "feed_timestamp"]
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
                "tags_filter": list_of_ids(),

                "show_only_displayed_in_feed": {"type": "boolean"}
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
                "query_text": name,
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
        "object_ids": non_empty_list_of_ids(),
        "added_tags": added_tags,
        "removed_tag_ids": removed_tag_ids
    }
}

objects_view_composite_hierarchy_elements_schema = {
    "type": "object",
    "required": ["object_id"],
    "additionalProperties": False,
    "properties": {
        "object_id": object_id
    }
}
