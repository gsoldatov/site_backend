# Incorrect user registration data
incorrect_user_attributes = {
    "login": [1, False, "", "a"*256],
    "password": [1, False, "a"*7, "a"*73],
    "password_repeat": [1, False, "a"*7, "a"*73],
    "username": [1, False, "", "a"*256],
    "user_level": [1, False, "wrong str"],
    "can_login": [1, "str"],
    "can_edit_objects": [1, "str"]
}
