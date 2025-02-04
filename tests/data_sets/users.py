# Incorrect user registration data
incorrect_user_attributes = {
    "login": [None, 1, False, "", "a"*256],
    "password": [None, 1, False, "a"*7, "a"*73],
    "password_repeat": [None, 1, False, "a"*7, "a"*73],
    "username": [None, 1, False, "", "a"*256],
    "user_level": [1, False, "wrong str"],
    "can_login": [1, "str"],
    "can_edit_objects": [1, "str"]
}
