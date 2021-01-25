# Link object data with or without object_type specified
link_object_data = {
    "required": ["link"],
    "additionalProperties": False,
    "properties": {
        "link": {
            "type": "string",
            "minLength": 1
        }
    }
}

link_object_type_and_data = {
    "properties": {
        "object_type": {
            "const": "link"
        },
        "object_data": link_object_data
    }
}


# Markdown object data with or without object_type specified
markdown_object_data = {
    "required": ["raw_text"],
    "additionalProperties": False,
    "properties": {
        "raw_text": {
            "type": "string",
            "minLength": 1
        }
    }
}

markdown_object_type_and_data = {
    "properties": {
        "object_type": {
            "const": "markdown"
        },
        "object_data": markdown_object_data
    }
}


# To-do list object data with or without object_type specified
to_do_list_object_data = {
    "required": ["sort_type", "items"],
    "additionalProperties": False,
    "properties": {
        "sort_type": {
            "type": "string",
            "enum": ["default", "state"]
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["item_number", "item_state", "item_text", "commentary", "indent", "isExpanded"],
                "additionalProperties": False,
                "properties": {
                    "item_number": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "item_state": {
                        "type": "string",
                        "enum": ["active", "completed", "cancelled"]
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
                    "isExpanded": {
                        "type": "boolean"
                    }
                }
            }
        }
    }
}

to_do_list_object_type_and_data = {
    "properties": {
        "object_type": {
            "const": "to_do_list"
        },
        "object_data": to_do_list_object_data
    }
}


# List of possible object_type and object_data combinations
object_type_and_data_options = [ link_object_type_and_data, markdown_object_type_and_data, to_do_list_object_type_and_data ]
