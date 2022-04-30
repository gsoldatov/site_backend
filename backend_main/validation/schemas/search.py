from backend_main.validation.schemas.common import name


search_schema = {
    "type": "object",
    "required": ["query"],
    "additionalProperties": False,
    "properties": {
        "query": {
            "type": "object",
            "required": ["query_text", "page", "items_per_page"],
            "additionalProperties": False,
            "properties": {
                "query_text": name,
                "page": {
                    "type": "integer",
                    "minimum": 1
                },
                "items_per_page": {
                    "type": "integer",
                    "minimum": 1
                }
            }
        }
    }
}
