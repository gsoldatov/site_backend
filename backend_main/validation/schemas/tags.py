from backend_main.validation.schemas.common import non_empty_list_of_ids, list_of_ids, object_id, name, description
from backend_main.validation.schemas.objects_tags import added_object_ids, removed_object_ids


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
