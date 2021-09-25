from backend_main.schemas.common import non_empty_list_of_ids


users_view_schema = {
    "type": "object",
    "required": ["user_ids"],
    "additionalProperties": False,
    "properties": {
        "full_view_mode": { "type": "boolean" },
        "user_ids": non_empty_list_of_ids()
    }
}
