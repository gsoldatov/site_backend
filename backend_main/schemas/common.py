def non_empty_list_of_ids(max_items = 1000, unique = True):
    return {
        "type": "array",
        "uniqueItems": unique,
        "minItems": 1,
        "maxItems": max_items,
        "items": object_id
    }

def list_of_ids(max_items = 1000, unique = True):
    return {
        "type": "array",
        "uniqueItems": unique,
        "maxItems": max_items,
        "items": object_id
    }

object_id = {
    "type": "integer",
    "minimum": 1
}

name = {
    "type": "string",
    "minLength": 1,
    "maxLength": 255
}

description = {
    "type": "string"
}

object_types_enum = ["link", "markdown", "to_do_list", "composite"]

is_published = {
    "type": "boolean"
}

password = {
    "type": "string",
    "minLength": 8,
    "maxLength": 72
}

user_level = {
    "type": "string",
    "enum": ["admin", "user"]
}

show_description_composite = {
    "type": "string",
    "enum": ["yes", "no", "inherit"]
}