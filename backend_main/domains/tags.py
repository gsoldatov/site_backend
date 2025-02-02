from aiohttp import web

from backend_main.auth.route_access.common import forbid_non_admin_adding_non_published_tag

from backend_main.db_operations.tags import add_tag as _add_tag, \
    update_tag as _update_tag, view_tags as _view_tags, delete_tags as _delete_tags, \
    view_page_tag_ids as _view_page_tag_ids, search_tags as _search_tags

from backend_main.util.exceptions import TagsNotFound
from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_tags

from backend_main.types.request import Request, request_log_event_key
from backend_main.types.domains.tags import Tag, AddedTag, \
    TagsPaginationInfo, TagsPaginationInfoWithResult, TagsSearchQuery


async def add_tag(request: Request, added_tag: AddedTag) -> Tag:
    # Forbid to add non-published tags for non-admins
    forbid_non_admin_adding_non_published_tag(request, added_tag)

    # Add tag and trigger searchables update
    tag = await _add_tag(request, added_tag)
    add_searchable_updates_for_tags(request, [tag.tag_id])

    # Log and return result
    request[request_log_event_key]("INFO", "domain", "Added tag.", details={"tag_id": tag.tag_id})
    return tag


async def update_tag(request: Request, tag: Tag) -> Tag:
    # Forbid to add non-published tags for non-admins
    forbid_non_admin_adding_non_published_tag(request, tag)

    try:
        # Update tag and trigger searchables update
        updated_tag = await _update_tag(request, tag)
        add_searchable_updates_for_tags(request, [tag.tag_id])

        # Log and return result
        request[request_log_event_key]("INFO", "domain", "Updated tag.", details={"tag_id": tag.tag_id})
        return updated_tag

    except TagsNotFound as e:
        # Handle non-existing tag update
        request[request_log_event_key]("WARNING", "domain", e.msg, details=e.details)
        raise web.HTTPNotFound(text=error_json(e.msg), content_type="application/json")


async def view_tags(request: Request, tag_ids: list[int]) -> list[Tag]:
    try:
        return await _view_tags(request, tag_ids)
    except TagsNotFound as e:
        request[request_log_event_key]("WARNING", "domain", e.msg, details=e.details)
        raise web.HTTPNotFound(text=error_json(e.msg), content_type="application/json")


async def delete_tags(request: Request, tag_ids: list[int]) -> None:
    try:
        await _delete_tags(request, tag_ids)
    except TagsNotFound as e:
        request[request_log_event_key]("WARNING", "domain", e.msg, details=e.details)
        raise web.HTTPNotFound(text=error_json(e.msg), content_type="application/json")


async def view_page_tag_ids(
    request: Request,
    pagination_info: TagsPaginationInfo
) -> TagsPaginationInfoWithResult:
    try:
        return await _view_page_tag_ids(request, pagination_info)
    except TagsNotFound as e:
        request[request_log_event_key]("WARNING", "domain", e.msg, e.details)
        raise web.HTTPNotFound(text=error_json(e.msg), content_type="application/json")


async def search_tags(request: Request, query: TagsSearchQuery) -> list[int]:
    try:
        return await _search_tags(request, query)
    except TagsNotFound as e:
        request[request_log_event_key]("WARNING", "domain", e.msg, e.details)
        raise web.HTTPNotFound(text=error_json(e.msg), content_type="application/json")
