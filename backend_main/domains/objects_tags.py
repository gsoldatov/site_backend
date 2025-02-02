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
from backend_main.types.domains.objects_tags import ObjectTag, ObjectIDAndAddedTags, ObjectIDAndRemovedTagIDs, \
    ObjectsTagsLists, ObjectsTagsMap


async def bulk_add_objects_tags(
        request: Request,
        objects_ids_and_added_tags: list[ObjectIDAndAddedTags]
    ) -> list[ObjectTag]:
    """
    Tags each object from `objects_ids_and_added_tags` with its added tags.
    Adds strings as new tags.
    """
    # Handle empty list & no added tags
    if len(objects_ids_and_added_tags) == 0: return []
    if not any((len(o.added_tags) > 0 for o in objects_ids_and_added_tags)): return []

    # Authorize objects modification
    object_ids = [o.object_id for o in objects_ids_and_added_tags]
    await authorize_objects_modification(request, object_ids)

    # Get added tag names
    lower_tag_names: set[str] = set()
    added_tag_names: list[str] = []
    for o in objects_ids_and_added_tags:
        for t in o.added_tags:
            if isinstance(t, str) and (t_lower := t.lower()) not in lower_tag_names:
                lower_tag_names.add(t_lower)
                added_tag_names.append(t)
    
    # Authorize adding new tags (forbid for non-admins)
    if len(added_tag_names) > 0: authorize_tag_modification(request)

    # Add new tags
    lower_tag_names_to_id_map = await _add_tags_by_name(request, added_tag_names)

    if len(new_tag_ids := list(lower_tag_names_to_id_map.map.values())) > 0:    
        # Add new tags as pending for `searchables` update
        request[request_log_event_key]("INFO", "domain","Added new tags by name.", details={"tag_ids": new_tag_ids})
        add_searchable_updates_for_tags(request, new_tag_ids)
    
    # Get pairs of inserted objects tags and map string tags to their IDs
    objects_tags = list(set((ObjectTag(
            object_id=o.object_id,
            tag_id=lower_tag_names_to_id_map.map[t.lower()] if isinstance(t, str) else t
        ) for o in objects_ids_and_added_tags for t in o.added_tags
    )))

    # Authorize adding tags to objects
    await authorize_objects_tagging(request, [ot.tag_id for ot in objects_tags])

    try:
        # Add objects tags
        await _add_objects_tags(request, objects_tags)
        request[request_log_event_key]("INFO", "domain", "Added objects' tags.",
            details={"objects_tags": [ot.model_dump_json() for ot in objects_tags]})
        return objects_tags
    
    except ObjectsTagsNotFound as e:
        # Handle non-existing objects & tags
        request[request_log_event_key]("INFO", "domain", e.msg, e.details)
        raise web.HTTPBadRequest(text=error_json(e.msg), content_type="application/json")


async def add_objects_tags(request: Request, object_ids: list[int], tags: list[int | str]) -> ObjectsTagsLists:
    """
    Tags objects with `object_ids` with `tags`.
    Processes string values from `tags` into new tags or maps to existing ones before tagging.
    """
    # Convert input data, add objects tags and return result
    objects_ids_and_added_tags = [ObjectIDAndAddedTags(object_id=o, added_tags=tags) for o in object_ids]
    added_objects_tags = await bulk_add_objects_tags(request, objects_ids_and_added_tags)
    return ObjectsTagsLists(
        # Remove duplicates in returned data
        object_ids=list(set(object_ids)),
        tag_ids=list(set((ot.tag_id for ot in added_objects_tags)))
    )


async def view_objects_tags(request: Request, object_ids: list[int]) -> ObjectsTagsMap:
    return await _view_objects_tags(request, object_ids)


async def view_tags_objects(request: Request, tag_ids: list[int]) -> ObjectsTagsMap:
    return await _view_tags_objects(request, tag_ids)


async def bulk_delete_objects_tags(
        request: Request,
        objects_ids_and_removed_tag_ids: list[ObjectIDAndRemovedTagIDs]
    ) -> list[ObjectTag]:
    """ Removes tags from each object specified in `objects_ids_and_added_tags`. """
    # Handle empty list & no removed tag IDs
    if len(objects_ids_and_removed_tag_ids) == 0: return []
    if not any((len(o.removed_tag_ids) > 0 for o in objects_ids_and_removed_tag_ids)): return []
    
    # Authorize object modification & tagging
    object_ids = [o.object_id for o in objects_ids_and_removed_tag_ids]
    tag_ids = list(set((t for o in objects_ids_and_removed_tag_ids for t in o.removed_tag_ids)))
    await authorize_objects_modification(request, object_ids)
    await authorize_objects_tagging(request, tag_ids)

    # Delete objects tags
    objects_tags = list(set((
        ObjectTag(object_id=o.object_id, tag_id=t)
        for o in objects_ids_and_removed_tag_ids for t in o.removed_tag_ids
    )))
    await _delete_objects_tags(request, objects_tags)
    return objects_tags


async def delete_objects_tags(request: Request, object_ids: list[int], tag_ids: list[int]) -> ObjectsTagsLists:
    """ Removes all tags with `tag_ids` from `object_ids`. """
    # Convert input data, add objects tags and return result
    object_ids_and_removed_tag_ids = [ObjectIDAndRemovedTagIDs(object_id=o, removed_tag_ids=tag_ids) for o in object_ids]
    removed_objects_tags = await bulk_delete_objects_tags(request, object_ids_and_removed_tag_ids)
    return ObjectsTagsLists(
        # Remove duplicates in returned data
        object_ids=list(set(object_ids)),
        tag_ids=list(set((ot.tag_id for ot in removed_objects_tags)))
    )
