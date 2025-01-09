from aiohttp import web

from backend_main.auth.route_access.common import forbid_non_admin_adding_non_published_tag

from backend_main.db_operations2.tags import add_tag as _add_tag, \
    update_tag as _update_tag

from backend_main.util.exceptions import TagNotFound
from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_tags

from backend_main.types.request import Request, request_log_event_key
from backend_main.types.domains.tags import Tag, AddedTag


async def add_tag(request: Request, added_tag: AddedTag) -> Tag:
    # Forbid to add non-published tags for non-admins
    forbid_non_admin_adding_non_published_tag(request, added_tag)

    # Add tag and trigger searchables update
    tag = await _add_tag(request, added_tag)
    add_searchable_updates_for_tags(request, [tag.tag_id])

    # Log and return result
    request[request_log_event_key]("INFO", "domain", "Added tag.", details=f"tag_id = {tag.tag_id}")
    return tag


async def update_tag(request: Request, tag: Tag) -> Tag:
    # Forbid to add non-published tags for non-admins
    forbid_non_admin_adding_non_published_tag(request, tag)

    try:
        # Update tag and trigger searchables update
        updated_tag = await _update_tag(request, tag)
        add_searchable_updates_for_tags(request, [tag.tag_id])

        # Log and return result
        request[request_log_event_key]("INFO", "domain", "Updated tag.", details=f"tag_id = {tag.tag_id}")
        return updated_tag

    except TagNotFound:
        # Handle non-existing tag update
        msg = "Tag not found."
        request[request_log_event_key]("WARNING", "domain", msg, details=f"tag_id = {tag.tag_id}")
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")
