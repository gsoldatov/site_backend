from backend_main.db_operations2.settings import update_settings as _update_settings

from backend_main.middlewares.connection import start_transaction

from backend_main.types.request import Request
from backend_main.types.domains.settings import SerializedSettings


async def update_settings(request: Request, serialized_settings: SerializedSettings) -> None:
    await start_transaction(request)
    return await _update_settings(request, serialized_settings)
