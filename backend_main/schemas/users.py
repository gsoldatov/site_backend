from backend_main.schemas.common import non_empty_list_of_ids, object_id, password, name, user_level


users_update_schema = {
    "type": "object",
    "required": ["user", "token_owner_password"],
    "additionalProperties": False,
    "properties": {
        "user": {
            "type": "object",
            "required": ["user_id"],
            "anyOf": [
                {"required": ["login"]},
                {"required": ["username"]},
                {"required": ["password"]},
                {"required": ["user_level"]},
                {"required": ["can_login"]},
                {"required": ["can_edit_objects"]}
            ],

            "additionalProperties": False,
            "properties": {
                "user_id": object_id,
                "login": name,
                "username": name,
                "password": password,
                "password_repeat": password,
                "user_level": user_level,
                "can_login": { "type": "boolean" },
                "can_edit_objects": { "type": "boolean" }
            },
            "dependencies": {
                "password": ["password_repeat"]
            }
        },
        
        "token_owner_password": password
    }
}


users_view_schema = {
    "type": "object",
    "required": ["user_ids"],
    "additionalProperties": False,
    "properties": {
        "full_view_mode": { "type": "boolean" },
        "user_ids": non_empty_list_of_ids()
    }
}
