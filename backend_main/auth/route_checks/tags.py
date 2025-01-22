from aiohttp import web
from sqlalchemy import select, func, and_

from backend_main.auth.route_access.common import forbid_anonymous, forbid_authenticated_non_admins

from backend_main.util.json import error_json

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_user_info_key, request_connection_key, request_log_event_key


def authorize_tag_modification(request: Request) -> None:
    """ Forbids tag modification by non-admins. """
    forbid_anonymous(request)
    forbid_authenticated_non_admins(request)


async def authorize_objects_tagging(request: Request, tag_ids: list[int]) -> None:
    """
    Forbids anonymous `request` issuers.
    Raises 403, if `request` is issued by a non-admin and any tag from `tag_ids` is not published.
    """
    forbid_anonymous(request)
    
    if request[request_user_info_key].user_level == "admin": return
    if len(tag_ids) == 0: return

    tags = request.config_dict[app_tables_key].tags

    result = await request[request_connection_key].execute(
        select(func.count())
        .select_from(tags)
        .where(and_(
            tags.c.tag_id.in_(tag_ids),
            tags.c.is_published == False
        ))
    )

    if (await result.fetchone())[0] > 0:
        msg = "Attempted to add non-published tags as a non-admin."
        request[request_log_event_key]("WARNING", "auth", msg, details=f"All tag_ids = ${tag_ids}")
        raise web.HTTPForbidden(text=error_json(msg), content_type="application/json")
