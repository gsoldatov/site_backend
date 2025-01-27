from aiohttp import web

from backend_main.auth.route_checks.objects import authorize_objects_modification, authorize_object_owner_modification
from backend_main.domains.users import ensure_user_ids_exist

from backend_main.db_operations.objects.attributes import add_objects as _add_objects, \
    update_objects as _update_objects, \
    update_modified_at as _update_modified_at, \
    view_objects_attributes_and_tags as _view_objects_attributes_and_tags, \
    view_existing_object_ids as _view_existing_object_ids

from backend_main.util.exceptions import UserNotFound, ObjectsNotFound
from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_objects

from datetime import datetime
from backend_main.types.request import Request, request_log_event_key
from backend_main.types.domains.objects.general import ObjectsIDsMap
from backend_main.types.domains.objects.attributes import UpsertedObjectAttributes, ObjectAttributesAndTags, ObjectType


async def add_objects(request: Request, objects_attributes: list[UpsertedObjectAttributes]) -> ObjectsIDsMap:
    # Check if `owner_id` values can be set by request issuer
    authorize_object_owner_modification(request, objects_attributes)

    try:
        # Add objects and trigger searchables update
        objects_ids_mapping = await _add_objects(request, objects_attributes)        
        add_searchable_updates_for_objects(request, [object_id for object_id in objects_ids_mapping.map.values()])
        return objects_ids_mapping
    
    except UserNotFound as e:
        request[request_log_event_key]("WARNING", "domain", str(e))
        raise web.HTTPBadRequest(text=error_json("User(-s) not found."), content_type="application/json")


async def update_objects(request: Request, objects_attributes: list[UpsertedObjectAttributes]) -> None:
    # Check if user can update objects
    object_ids = [o.object_id for o in objects_attributes]
    await authorize_objects_modification(request, object_ids)

    # Check if assigned object owners exist
    user_ids = list({o.owner_id for o in objects_attributes})
    await ensure_user_ids_exist(request, user_ids)

    # Check if `owner_id` values can be set by request issuer
    authorize_object_owner_modification(request, objects_attributes)

    try:
        # Update objects and trigger searchables update
        await _update_objects(request, objects_attributes)
        add_searchable_updates_for_objects(request, [o.object_id for o in objects_attributes])

    except ObjectsNotFound as e:
        # Handle attempts to update non-existing objects
        request[request_log_event_key]("WARNING", "domain", str(e))
        raise web.HTTPBadRequest(text=error_json(str(e)), content_type="application/json")


async def update_modified_at(request: Request, object_ids: list[int], modified_at: datetime) -> datetime:
    # Authorize update operation
    await authorize_objects_modification(request, object_ids)

    # Update attribute & return
    return await _update_modified_at(request, object_ids, modified_at)


async def view_objects_attributes_and_tags(request: Request, object_ids: list[int]) -> list[ObjectAttributesAndTags]:
    if len(object_ids) == 0: return []
    return await _view_objects_attributes_and_tags(request, object_ids)


async def ensure_objects_types(request: Request, object_ids: list[int], object_types: list[ObjectType]) -> None:
    """ Ensures all `object_ids` exist in the database and have provided `object_type`. """
    if len(object_ids) == 0: return
    object_ids_set = set(object_ids)
    existing_object_ids = await _view_existing_object_ids(request, object_ids_set, object_types)
    if len(non_existing_object_ids := object_ids_set.difference(existing_object_ids)) > 0:
        raise ObjectsNotFound(f"Objects {non_existing_object_ids} don't belong to the types {object_types}.")
