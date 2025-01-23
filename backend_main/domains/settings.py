from backend_main.db_operations.settings import update_settings as _update_settings, \
    view_settings as _view_settings

from backend_main.types.request import Request
from backend_main.types.domains.settings import SerializedSettings, Setting


async def update_settings(request: Request, serialized_settings: SerializedSettings) -> None:
    return await _update_settings(request, serialized_settings)


async def view_settings(request: Request, setting_names: list[str] | None) -> list[Setting]:
    return await _view_settings(request, setting_names)
