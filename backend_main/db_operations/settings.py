"""
Database operations with app settings.
"""
from sqlalchemy import select, true
from sqlalchemy.dialects.postgresql import insert

from backend_main.auth.route_access.common import forbid_anonymous, forbid_authenticated_non_admins

from backend_main.util.settings import serialize_settings, deserialize_setting

from backend_main.types.app import app_tables_key
from backend_main.types.request import request_connection_key


async def update_settings(request, settings):
    """
    Serializes and update setting values provided in the `setting` dict.
    """
    data = serialize_settings(settings)
    settings = request.config_dict[app_tables_key].settings

    insert_stmt = insert(settings).values(data)
    
    await request[request_connection_key].execute(
        insert_stmt
        .on_conflict_do_update(
            index_elements=[settings.c.setting_name],
            # On conflict get the correct value for update from the conflicted row via 'excluded' prop of the statement
            set_=dict(setting_value=insert_stmt.excluded.setting_value)
        )
    )


async def view_settings(request, setting_names = None):
    """
    Returns the settings specified in `setting_names` (or all app settings if it's omitted).
    """
    # Auth checks for view all settings case (debounce non-admins)
    if setting_names is None:
        forbid_anonymous(request)
        forbid_authenticated_non_admins(request)
    
    settings = request.config_dict[app_tables_key].settings
    clause = settings.c.setting_name.in_(setting_names) if setting_names is not None else true()

    result = await request[request_connection_key].execute(
        select(settings.c.setting_name, settings.c.setting_value, settings.c.is_public)
        .where(clause)
    )

    deserialized_settings = {}
    # Deserialize settings and check if they can be returned to non-admins
    for row in await result.fetchall():
        # Private settings can only be viewed by admins (skip double check if all settings are being returned)
        if not row[2] and setting_names is not None:
            forbid_anonymous(request)
            forbid_authenticated_non_admins(request)
        
        deserialized_settings[row[0]] = deserialize_setting(row[0], row[1])
    return deserialized_settings
