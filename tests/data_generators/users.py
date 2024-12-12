from datetime import datetime, timezone


def get_test_user(user_id, registered_at = None, login = None, password = None, password_repeat = None, username = None,
    user_level = None, can_login = None, can_edit_objects = None, pop_keys = []):
    """
    Returns a new dictionary for `users` table and auth route tests with attributes specified in `pop_keys` popped from it.
    `user_id` value is provided as the first argument, other user attributes can be optionally provided to override default values.
    """
    registered_at = registered_at if registered_at is not None else datetime.now(tz=timezone.utc)
    login = login if login is not None else f"login {user_id}"
    password = password if password is not None else f"password {user_id}"
    password_repeat = password_repeat if password_repeat is not None else password
    username = username if username is not None else f"username {user_id}"
    user_level = user_level if user_level is not None else "user"
    can_login = can_login if can_login is not None else True
    can_edit_objects = can_edit_objects if can_edit_objects is not None else True
    
    user = {"user_id": user_id, "registered_at": registered_at, "login": login, "password": password, "password_repeat": password_repeat,
        "username": username, "user_level": user_level, "can_login": can_login, "can_edit_objects": can_edit_objects}
    for k in pop_keys:
        user.pop(k, None)
    return user


def get_update_user_request_body(user = None, token_owner_password = None):
    """
    Returns a valid request body for /update/users route.
    `user` and `token_owner_password` are respective JSON attributes of the request body.
    """
    if token_owner_password is None: raise TypeError("`token_owner_password` is required.")

    if user is None:
        user = get_test_user(1, pop_keys=["registered_at"])
    
    return {"user": user, "token_owner_password": token_owner_password}
