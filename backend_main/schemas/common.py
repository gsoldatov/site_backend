def non_empty_list_of_ids(max_items = 1000):
    return {
        "type": "array",
        "uniqueItems": True,
        "minItems": 1,
        "maxItems": max_items,
        "items": {
            "type": "integer",
            "minimum": 1
        }
    }

def list_of_ids(max_items = 1000):
    return {
        "type": "array",
        "uniqueItems": True,
        "maxItems": 1000,
        "items": {
            "type": "integer",
            "minimum": 1
        }
    }