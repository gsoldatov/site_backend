from aiohttp import web

from backend_main.auth.route_checks.objects import authorize_objects_modification
from backend_main.auth.route_checks.tags import authorize_tag_modification, authorize_objects_tagging

from backend_main.db_operations.objects_tags import \
    add_objects_tags as _add_objects_tags, \
    view_objects_tags as _view_objects_tags, \
    view_tags_objects as _view_tags_objects, \
    delete_objects_tags as _delete_objects_tags
from backend_main.db_operations.tags import add_tags_by_name as _add_tags_by_name

from backend_main.util.exceptions import ObjectsTagsNotFound
from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_tags

from backend_main.types.request import Request, request_log_event_key
from backend_main.types.domains.objects_tags import ObjectsTagsLists, ObjectsTagsMap


async def add_objects_tags(request: Request, object_ids: list[int], tags: list[int | str]) -> ObjectsTagsLists:
    """
    Tags objects with `object_ids` with `tags`.
    Processes string values from `tags` into new tags or maps to existing ones before tagging.
    """
    # Handle empty lists
    if len(object_ids) == 0 or len(tags) == 0: return ObjectsTagsLists(object_ids=[], tag_ids=[])
    
    # Remove duplicate string and numeric tags
    tags_set: set[int | str] = set()
    unique_tags: list[int | str] = []
    for t in tags:
        if isinstance(t, int):
            if t not in tags_set:
                unique_tags.append(t)
                tags_set.add(t)
        else:
            if t.lower() not in tags_set:
                unique_tags.append(t)
                tags_set.add(t.lower())
    tags = unique_tags

    # Run auth checks
    added_tag_names = [t for t in tags if isinstance(t, str)]
    await authorize_objects_modification(request, object_ids)
    
    if len(added_tag_names) > 0:    # forbid creating new tags for non-admins
        authorize_tag_modification(request)
    
    # Add new tags
    added_tag_names_to_id_map = await _add_tags_by_name(request, added_tag_names)

    if len(new_tag_ids := list(added_tag_names_to_id_map.map.values())) > 0:    
        # Add new tags as pending for `searchables` update
        request[request_log_event_key]("INFO", "domain","Added new tags by name.", details=f"tag_ids = {new_tag_ids}")
        add_searchable_updates_for_tags(request, new_tag_ids)

    # Get added tag IDs list & remove duplicate object & tag IDs
    # (handle case, where tag is passed both as a string & as an ID)
    object_ids = list(set(object_ids))
    added_tag_ids = list(set(
        [t if isinstance(t, int) else added_tag_names_to_id_map.map[t] for t in tags]
    ))

    # Run auth checks, pt. 2
    if len(added_tag_ids) > 0:
        await authorize_objects_tagging(request, added_tag_ids)
    
    # Add objects tags
    try:
        await _add_objects_tags(request, object_ids, added_tag_ids)

        request[request_log_event_key]("INFO", "domain", "Added objects' tags.",
            details=f"object_ids = {object_ids} tag_ids = {added_tag_ids}")

        return ObjectsTagsLists(object_ids=object_ids, tag_ids=added_tag_ids)
    except ObjectsTagsNotFound as e:
        request[request_log_event_key]("INFO", "domain", "Failed to add objects' tags.", details=str(e))
        raise web.HTTPBadRequest(text=error_json(e), content_type="application/json")


async def view_objects_tags(request: Request, object_ids: list[int]) -> ObjectsTagsMap:
    return await _view_objects_tags(request, object_ids)


async def view_tags_objects(request: Request, tag_ids: list[int]) -> ObjectsTagsMap:
    return await _view_tags_objects(request, tag_ids)


async def delete_objects_tags(request: Request, object_ids: list[int], tag_ids: list[int]) -> ObjectsTagsLists:
    """ Removes all tags with `tag_ids` from `object_ids`. """
    # Removed duplicates
    object_ids = list(set(object_ids))
    tag_ids = list(set(tag_ids))

    # Run auth checks
    await authorize_objects_modification(request, object_ids)
    await authorize_objects_tagging(request, tag_ids)

    # Delete objects tags
    await _delete_objects_tags(request, object_ids, tag_ids)

    return ObjectsTagsLists(object_ids=object_ids, tag_ids=tag_ids)
