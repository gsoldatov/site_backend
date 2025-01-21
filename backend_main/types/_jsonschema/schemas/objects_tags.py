from backend_main.types._jsonschema.schemas.common import list_of_ids, object_id, name


added_tags = {
    "type": "array",
    "maxItems": 100,
    "items": {
        "oneOf": [object_id, name]
    }
}
removed_tag_ids = list_of_ids(max_items = 100, unique = False)
