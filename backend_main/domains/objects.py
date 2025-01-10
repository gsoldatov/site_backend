from backend_main.auth.route_checks.objects import authorize_objects_modification

from backend_main.db_operations2.objects.general import \
    get_exclusive_subobject_ids as _get_exclusive_subobject_ids, \
    delete_objects as _delete_objects

from backend_main.util.exceptions import ObjectsNotFound

from backend_main.types.request import Request, request_log_event_key


async def delete_objects(request: Request, object_ids: list[int], delete_subobjects: bool) -> None:
    # Get full list of objects to delete
    # (include subobjects, exclusive to `object_ids`, if `delete_subobjects` is true)
    subobject_ids_to_delete = await _get_exclusive_subobject_ids(request, object_ids) \
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
