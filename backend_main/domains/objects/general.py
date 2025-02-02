from aiohttp import web

from backend_main.auth.route_checks.objects import authorize_objects_modification

from backend_main.db_operations.objects.data.composite import view_exclusive_subobject_ids as _view_exclusive_subobject_ids
from backend_main.db_operations.objects.general import view_page_object_ids as _view_page_object_ids, \
    search_objects as _search_objects, view_composite_hierarchy as _view_composite_hierarchy, delete_objects as _delete_objects

from backend_main.util.exceptions import ObjectsNotFound, ObjectIsNotComposite
from backend_main.util.json import error_json

from collections.abc import Collection
from backend_main.types.request import Request, request_log_event_key
from backend_main.types.domains.objects.general import ObjectsPaginationInfo, \
    ObjectsPaginationInfoWithResult, ObjectsSearchQuery, CompositeHierarchy, \
    ObjectsIDsMap, UpsertedObject, UpsertedComposite


async def view_page_object_ids(
        request: Request,
        pagination_info: ObjectsPaginationInfo
    ) -> ObjectsPaginationInfoWithResult:
    try:
        return await _view_page_object_ids(request, pagination_info)
    except ObjectsNotFound as e:
        request[request_log_event_key]("WARNING", "domain", e.msg, e.details)
        raise web.HTTPNotFound(text=error_json(e.msg), content_type="application/json")


async def search_objects(request: Request, query: ObjectsSearchQuery) -> list[int]:
    try:
        return await _search_objects(request, query)
    except ObjectsNotFound as e:
        request[request_log_event_key]("WARNING", "domain", e.msg, e.details)
        raise web.HTTPNotFound(text=error_json(e.msg), content_type="application/json")


async def view_composite_hierarchy(request: Request, object_id: int) -> CompositeHierarchy:
    try:
        return await _view_composite_hierarchy(request, object_id)
    except ObjectsNotFound as e:
        request[request_log_event_key]("WARNING", "domain", e.msg, e.details)
        raise web.HTTPNotFound(text=error_json(e.msg), content_type="application/json")
    except ObjectIsNotComposite as e:
        request[request_log_event_key]("WARNING", "domain", e.msg, e.details)
        raise web.HTTPBadRequest(text=error_json(e.msg), content_type="application/json")


async def delete_objects(request: Request, object_ids: Collection[int], delete_subobjects: bool) -> None:
    # Get full list of objects to delete
    # (include subobjects, exclusive to `object_ids`, if `delete_subobjects` is true)
    if not isinstance(object_ids, list): object_ids = list(object_ids)
    subobject_ids_to_delete = await _view_exclusive_subobject_ids(request, object_ids) \
        if delete_subobjects else []
    deleted_object_ids = list(set(object_ids + subobject_ids_to_delete))

    # Authorize delete operation
    await authorize_objects_modification(request, deleted_object_ids)

    # Delete objects
    try:
        await _delete_objects(request, deleted_object_ids)
        request[request_log_event_key]("INFO", "domain", "Deleted objects.",
                                       details={"object_ids": list(object_ids), "subobject_ids": subobject_ids_to_delete})
    except ObjectsNotFound as e:
        request[request_log_event_key]("WARNING", "domain", e.msg, e.details)
        # Don't raise 404, so that changes are committed
        # raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")


def map_objects_ids(objects: list[UpsertedObject], objects_ids_map: ObjectsIDsMap) -> list[UpsertedObject]:
    """
    Maps IDs of new objects and composite subobjects passed in request data
    to the values they were assigned in the database.
    """
    objects_with_mapped_ids: list[UpsertedObject] = []
    for object in objects:
        new_oobject = type(object).model_validate({
            **object.model_dump(), "object_id": objects_ids_map.map.get(object.object_id, object.object_id)
        })
        if isinstance(new_oobject, UpsertedComposite):
            for so in new_oobject.object_data.subobjects:
                so.subobject_id = objects_ids_map.map.get(so.subobject_id, so.subobject_id)
        objects_with_mapped_ids.append(new_oobject)
    return objects_with_mapped_ids
