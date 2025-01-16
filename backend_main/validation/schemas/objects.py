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
                    "feed_timestamp": {"type": ["string", "null"]},
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
                "feed_timestamp": {"type": ["string", "null"]},
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
