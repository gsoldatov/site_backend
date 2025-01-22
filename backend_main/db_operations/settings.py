"""
Database operations with app settings.
"""
from sqlalchemy import select, true
from sqlalchemy.dialects.postgresql import insert

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.settings import Setting, SerializedSettings


async def update_settings(request: Request, serialized_settings: SerializedSettings) -> None:
    """
    Updates values of settings provided in the `serialized_settings`.
    """
    settings = request.config_dict[app_tables_key].settings

    # Exit if no settings were updated
    updated_setting_names = {n for n in serialized_settings.model_fields.keys() 
                             if getattr(serialized_settings, n, None) is not None}
    if len(updated_setting_names) == 0: return

    # Query all modified rows from the table & build new rows to be inserted
    result = await request[request_connection_key].execute(
        select(settings.c.setting_name, settings.c.is_public)
        .where(settings.c.setting_name.in_(updated_setting_names))
    )

    values = [Setting(
        setting_name=row[0],
        setting_value=serialized_settings.deserialize_setting_value(row[0]),
        is_public=row[1]
    ).model_dump() for row in await result.fetchall()]

    # Update new rows (insert with on conflict update)
    insert_stmt = insert(settings).values(values)
    
    await request[request_connection_key].execute(
        insert_stmt
        .on_conflict_do_update(
            index_elements=[settings.c.setting_name],
            # On conflict get the correct value for update from the conflicted row via 'excluded' prop of the statement
            set_=dict(setting_value=insert_stmt.excluded.setting_value)
        )
    )


async def view_settings(request: Request, setting_names: list[str] | None) -> list[Setting]:
    """
    Returns the settings specified in `setting_names` (or all app settings if it's `None`).
    """
    # Handle empty `setting_names`
    if setting_names is not None and len(setting_names) == 0: return []

    # Auth checks for view all settings case (debounce non-admins)
    settings = request.config_dict[app_tables_key].settings
    clause = settings.c.setting_name.in_(setting_names) if setting_names is not None else true()

    result = await request[request_connection_key].execute(
        select(settings.c.setting_name, settings.c.setting_value, settings.c.is_public)
        .where(clause)
    )

    return [Setting.model_validate(dict(row)) for row in await result.fetchall()]
