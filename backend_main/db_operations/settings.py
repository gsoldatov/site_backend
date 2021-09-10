"""
Database operations with app settings.
"""
from sqlalchemy import select, true

from backend_main.auth.route_access_checks.util import debounce_anonymous, debounce_authenticated_non_admins


async def view_settings(request, setting_names = []):
    """
    Returns the settings specified in `setting_names` (or all app settings if it's omitted).
    """
    # Debounce non-admins
    debounce_anonymous(request)
    debounce_authenticated_non_admins(request)

    settings = request.app["tables"]["settings"]
    clause = settings.c.setting_name.in_(setting_names) if setting_names is not None else true()

    result = await request["conn"].execute(
        select([settings.c.setting_name, settings.c.setting_value])
        .where(clause)
    )

    return {row[0]: row[1] for row in await result.fetchall()}
