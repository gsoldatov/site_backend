from backend_main.schemas.common import non_empty_list_of_ids, list_of_ids, object_id, name, description, password
from backend_main.schemas.objects_tags import added_object_ids, removed_object_ids


register_schema = {
    "type": "object",
    "required": ["login", "password", "password_repeat", "username"],
    "additionalProperties": False,
    "properties": {
        "login": name,
        "password": password,
        "password_repeat": password,
        "username": name,

        "user_level": {
            "type": "string",
            "enum": ["admin", "user"]
        },
        "can_login": {"type": "boolean"},
        "can_edit_objects": {"type": "boolean"}
    }
}


login_schema = {
    "type": "object",
    "required": ["login", "password"],
    "additionalProperties": False,
    "properties": {
        "login": name,
        "password": {   # Don't limit password length in validation, return 401 manually if len(password) >= 72 (max size for bcrypt-encrypted passwords)
            "type": "string",
            "minLength": 1
        } 
    }
}