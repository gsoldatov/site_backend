from backend_main.auth.route_access.common import forbid_non_admin_adding_non_published_tag

from backend_main.db_operations2.tags import add_tag as _add_tag

from backend_main.util.searchables import add_searchable_updates_for_tags

from backend_main.types.request import Request, request_log_event_key
from backend_main.types.domains.tags import Tag, AddedTag


async def add_tag(request: Request, added_tag: AddedTag) -> Tag:
    # Forbid to add non-published tags for non-admins
    forbid_non_admin_adding_non_published_tag(request, added_tag)

    tag = await _add_tag(request, added_tag)

    # Add tag as pending for `searchables` update
    add_searchable_updates_for_tags(request, [tag.tag_id])

    # Log and return result
    request[request_log_event_key]("INFO", "db_operation", "Added tag.", details=f"tag_id = {tag.tag_id}")
    return tag
