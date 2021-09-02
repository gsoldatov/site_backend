from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.sql import and_ 



async def get_user_info(request):
    """
    Gets user information for the provided access token and adds it to `request.user_info`.
    Raises 401 if token is not found or expired.
    Prolongs the lifetime of the token if otherwise.
    """
    # Exit if anonymous
    if request.user_info.is_anonymous:
        return
    
    users = request.app["tables"]["users"]
    sessions = request.app["tables"]["sessions"]
    current_time = datetime.utcnow()
    expiration_time = current_time + timedelta(seconds=request.app["config"]["app"]["token_lifetime"])

    # Update expiration time and return user information corresponding to the updated token 
    # in a single query using CTE.
    # NOTE: values updated in CTE can't be fetched with select in the same query.
    update_cte = (
        sessions.update()
        .where(and_(
            sessions.c.access_token == request.user_info.access_token,
            sessions.c.expiration_time > current_time
        ))
        .values({"expiration_time": expiration_time})
        .returning(sessions.c.user_id.label("user_id"))
    ).cte("update_cte")

    result = await request["conn"].execute(
        select([users.c.user_id, users.c.user_level, users.c.can_edit_objects])
        .where(users.c.user_id.in_(select([update_cte.c.user_id])))
    )

    info = await result.fetchone()

    # Raise 401 if token was not found or expired
    if not info:
        raise web.HTTPUnauthorized(text=error_json("Invalid token."), content_type="application/json")
    
    ui = request.user_info
    ui.user_id, ui.user_level, ui.can_edit_objects = info
