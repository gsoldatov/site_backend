from copy import deepcopy

from backend_main.schemas.common import object_id, name, description, is_published
# from backend_main.schemas.objects_tags import added_tags, removed_tag_ids


# Link object data
link_object_data = {
    "type": "object",
    "required": ["link"],
    "additionalProperties": False,
    "properties": {
        "link": {
            "type": "string",
            "minLength": 1
        }
    }
}


# Markdown object data
markdown_object_data = {
    "type": "object",
    "required": ["raw_text"],
    "additionalProperties": False,
    "properties": {
        "raw_text": {
            "type": "string",
            "minLength": 1
        }
    }
}


# To-do list object data
to_do_list_object_data = {
    "type": "object",
    "required": ["sort_type", "items"],
    "additionalProperties": False,
    "properties": {
        "sort_type": {
            "type": "string",
            "enum": ["default", "state"]
        },
        "items": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["item_number", "item_state", "item_text", "commentary", "indent", "is_expanded"],
                "additionalProperties": False,
                "properties": {
                    "item_number": {
                        "type": "integer",
                        "minimum": 0
                    },
                    "item_state": {
                        "type": "string",
                        "enum": ["active", "completed", "optional", "cancelled"]
                    },
                    "item_text": {
                        "type": "string"
                    },
                    "commentary": {
                        "type": "string"
                    },
                    "indent": {
                        "type": "integer",
                        "minimum": 0
                    },
                    "is_expanded": {
                        "type": "boolean"
                    }
                }
            }
        }
    }
}


# Object data options without composite option
object_type_and_data_options_without_composite = {
    "link": link_object_data,
    "markdown": markdown_object_data,
    "to_do_list": to_do_list_object_data
}

# Composite subobject item options
composite_subobject_item_options = [{ 
    # Existing subobjects without data update
    "type": "object",
    "required": ["object_id", "row", "column", "selected_tab", "is_expanded"],
    "additionalProperties": False,
    "properties": {
        "object_id": object_id,
        "row": { "type": "integer", "minimum": 0 },
        "column": { "type": "integer", "minimum": 0 },
        "selected_tab": { "type": "integer", "minimum": 0 },
        "is_expanded": { "type": "boolean" }
    }
}]

composite_subobject_item_options.extend([{
    # New subobjects and existing subobjects with data updates (custom object_data for each object_type, composite subobjects are not allowed)
    "type": "object",
    "required": ["object_id", "row", "column", "selected_tab", "is_expanded",
                    "object_name", "object_description", "object_type", "is_published", "object_data"],
    "additionalProperties": False,    # added_tags and removed_tag_ids are optional (but currently not added => False)
    "properties": {                            
        "object_id": { "type": "integer" }, # can be negative for new objects
        "row": { "type": "integer", "minimum": 0 },
        "column": { "type": "integer", "minimum": 0 },
        "selected_tab": { "type": "integer", "minimum": 0 },
        "is_expanded": { "type": "boolean" },
        
        "object_name": name,
        "object_description": description,
        "object_type": {
            "const": object_type
        },
        "is_published": is_published,
        "owner_id": object_id,
        
        "object_data": object_type_and_data_options_without_composite[object_type]
        # "added_tags": added_tags,
        # "removed_tag_ids": removed_tag_ids,
    }
}
for object_type in object_type_and_data_options_without_composite])


# Composite object data with and without object_type specified
composite_object_data = {
    "type": "object",
    "required": ["subobjects", "deleted_subobjects"],
    "additionalProperties": False,
    "properties": {
        "subobjects": {
            "type": "array",
            "minItems": 1,
            "items": {
                "oneOf": composite_subobject_item_options
            }
        },

        "deleted_subobjects": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["object_id", "is_full_delete"],
                "additionalProperties": False,
                "properties": {
                    "object_id": object_id,
                    "is_full_delete": { "type": "boolean" }
                }
            }
        }
    }
}


# List of possible object_type and object_data combinations
object_type_and_data_options = deepcopy(object_type_and_data_options_without_composite)
object_type_and_data_options["composite"] = composite_object_data
