from backend_main.auth.route_access.common import forbid_anonymous, forbid_authenticated_non_admins

from backend_main.types.request import Request
from backend_main.types.domains.settings import Setting
from backend_main.types.routes.settings import SettingsViewRequestBody


def authorize_settings_view(request: Request, request_data: SettingsViewRequestBody) -> None:
    """ Ensures non-admins are not trying to view all settings. """    
    if request_data.view_all:
        forbid_anonymous(request)
        forbid_authenticated_non_admins(request)


def authorize_private_settings_return(request: Request, settings: list[Setting]) -> None:
    """ Ensures private app settings are not present in `settings`, if `request` was issued by a non-admin. """
    for setting in settings:
        # Check first private setting only
        if not setting.is_public:
            forbid_anonymous(request)
            forbid_authenticated_non_admins(request)
            return
