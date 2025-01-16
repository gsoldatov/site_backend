from aiohttp import web
from typing import get_args

from backend_main.auth.route_checks.objects import authorize_objects_modification

from backend_main.db_operations2.objects.general import view_exclusive_subobject_ids as _view_exclusive_subobject_ids, \
    view_page_object_ids as _view_page_object_ids, search_objects as _search_objects, \
    view_composite_hierarchy as _view_composite_hierarchy, delete_objects as _delete_objects
from backend_main.db_operations2.objects.attributes import update_modified_at as _update_modified_at, \
    view_objects_attributes_and_tags as _view_objects_attributes_and_tags, \
    view_objects_types as _view_objects_types
from backend_main.db_operations2.objects.links import view_links as _view_links
from backend_main.db_operations2.objects.markdown import view_markdown as _view_markdown
from backend_main.db_operations2.objects.to_do_lists import view_to_do_lists as _view_to_do_lists
from backend_main.db_operations2.objects.composite import view_composite as _view_composite

from backend_main.util.exceptions import ObjectsNotFound, ObjectIsNotComposite
from backend_main.util.json import error_json

from datetime import datetime
from backend_main.types.request import Request, request_log_event_key
from backend_main.types.domains.objects import ObjectAttributesAndTags, ObjectType, \
    ObjectIDTypeData, \
    ObjectsPaginationInfo, ObjectsPaginationInfoWithResult, ObjectsSearchQuery, CompositeHierarchy


async def update_modified_at(request: Request, object_ids: list[int], modified_at: datetime) -> datetime:
    # Authorize update operation
    await authorize_objects_modification(request, object_ids)

    # Update attribute & return
    return await _update_modified_at(request, object_ids, modified_at)


async def view_objects_attributes_and_tags(request: Request, object_ids: list[int]) -> list[ObjectAttributesAndTags]:
    if len(object_ids) == 0: return []
    return await _view_objects_attributes_and_tags(request, object_ids)


async def view_objects_data(request: Request, object_ids: list[int]) -> list[ObjectIDTypeData]:
    if len(object_ids) == 0: return []

    # Get object types of `object_ids`
    # (for multiple objects set all object types)
    object_types = await _view_objects_types(request, object_ids) \
        if len(object_ids) < 4 else get_args(ObjectType)
    
    # Query object data of each required type
    result: list[ObjectIDTypeData] = []
    
    if "link" in object_types:
        result += await _view_links(request, object_ids)
    if "markdown" in object_types:
        result += await _view_markdown(request, object_ids)
    if "to_do_list" in object_types:
        result += await _view_to_do_lists(request, object_ids)
    if "composite" in object_types:
        result += await _view_composite(request, object_ids)
    
    return result


async def view_page_object_ids(
        request: Request,
        pagination_info: ObjectsPaginationInfo
    ) -> ObjectsPaginationInfoWithResult:
    try:
        return await _view_page_object_ids(request, pagination_info)
    except ObjectsNotFound:
        msg = "No objects found."
        request[request_log_event_key]("WARNING", "domain", msg)
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")



async def search_objects(request: Request, query: ObjectsSearchQuery) -> list[int]:
    try:
        return await _search_objects(request, query)
    except ObjectsNotFound:
        msg = "No objects found."
        request[request_log_event_key]("WARNING", "domain", msg)
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")


async def view_composite_hierarchy(request: Request, object_id: int) -> CompositeHierarchy:
    try:
        return await _view_composite_hierarchy(request, object_id)
    except ObjectsNotFound:
        msg = "Object not found."
        request[request_log_event_key]("WARNING", "domain", msg, details=f"object_id = {object_id}")
        raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")
    except ObjectIsNotComposite:
        msg = "Attempted to loop through a hierarchy of a non-composite object."
        request[request_log_event_key]("WARNING", "domain", msg, details=f"object_id = {object_id}")
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")


async def delete_objects(request: Request, object_ids: list[int], delete_subobjects: bool) -> None:
    # Get full list of objects to delete
    # (include subobjects, exclusive to `object_ids`, if `delete_subobjects` is true)
    subobject_ids_to_delete = await _view_exclusive_subobject_ids(request, object_ids) \
        if delete_subobjects else []
    deleted_object_ids = list(set(object_ids + subobject_ids_to_delete))

    # Authorize delete operation
    await authorize_objects_modification(request, deleted_object_ids)

    # Delete objects
    try:
        await _delete_objects(request, deleted_object_ids)
        request[request_log_event_key]("INFO", "domain", "Deleted objects.",
                                       details=f"object_ids = {object_ids}, subobject_ids = {subobject_ids_to_delete}")
    except ObjectsNotFound:
        msg = "Attempted to delete non-existing object(-s)."
        request[request_log_event_key]("WARNING", "domain", msg, details=f"object_ids = {object_ids}")
        # Don't raise 404, so that changes are committed
        # raise web.HTTPNotFound(text=error_json(msg), content_type="application/json")

