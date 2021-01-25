def non_empty_list_of_ids(max_items = 1000, unique = True):
    return {
        "type": "array",
        "uniqueItems": unique,
        "minItems": 1,
        "maxItems": max_items,
        "items": {
            "type": "integer",
            "minimum": 1
        }
    }

def list_of_ids(max_items = 1000, unique = True):
    return {
        "type": "array",
        "uniqueItems": unique,
        "maxItems": max_items,
        "items": {
            "type": "integer",
            "minimum": 1
        }
    }
