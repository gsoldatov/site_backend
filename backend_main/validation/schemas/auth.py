from backend_main.validation.schemas.common import name, password, user_level


register_schema = {
    "type": "object",
    "required": ["login", "password", "password_repeat", "username"],
    "additionalProperties": False,
    "properties": {
        "login": name,
        "password": password,
        "password_repeat": password,
        "username": name,

        "user_level": user_level,
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