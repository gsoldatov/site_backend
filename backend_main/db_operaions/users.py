"""
User-related database operations.
"""
from sqlalchemy import select


async def check_if_user_ids_exist(request, user_ids):
    """
    Checks if provided `user_id` exists in the database.
    Raises 400 if not.
    """
    if len(user_ids) == 0:
        return
    users = request.app["tables"]["users"]

    result = await request["conn"].execute(
        select([users.c.user_id])
        .where(users.c.user_id.in_(user_ids))
    )
    existing_user_ids = set(await result.fetchone())

    if len(user_ids) > len(existing_user_ids):
        non_existing_user_ids = set(user_ids).difference(existing_user_ids)
        raise web.HTTPBadRequest(text=error_json(f"User IDs '{non_existing_user_ids}' do not exist."), content_type="application/json")
        