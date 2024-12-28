from backend_main.util.constants import forbidden_non_admin_user_modify_attributes
from backend_main.util.exceptions import InvalidNewUserAttributesException

from backend_main.types.routes.auth import AuthRegisterRequestBody
from backend_main.types.domains.users import NewUser
from backend_main.types.request import Request, request_user_info_key, request_time_key


async def validate_new_user_data(request: Request) -> NewUser:
    """
    Validates request data for /auth/register route
    """
    request_user_data = AuthRegisterRequestBody.model_validate(await request.json())

    # Check if non-admins are trying to set privileges
    # TODO move to auth checks
    if request[request_user_info_key].user_level != "admin":
        for attr in forbidden_non_admin_user_modify_attributes:
            if getattr(request_user_data, attr) is not None:
                raise InvalidNewUserAttributesException()
    
    # Set missing values to defaults
    user_attributes = {
        "registered_at": request[request_time_key],
        "user_level": "user",
        "can_login": True,
        "can_edit_objects": True
    }
    user_attributes.update(
        request_user_data.model_dump(exclude_none=True)
    )
    
    return NewUser.model_validate(user_attributes)
