from aiohttp import web
from typing import get_args

from backend_main.db_operations.objects.attributes import view_objects_types as _view_objects_types
from backend_main.db_operations.objects.data.links import upsert_links as _upsert_links, view_links as _view_links
from backend_main.db_operations.objects.data.markdown import \
    upsert_markdown as _upsert_markdown, view_markdown as _view_markdown
from backend_main.db_operations.objects.data.to_do_lists import \
    upsert_to_do_lists as _upsert_to_do_lists, view_to_do_lists as _view_to_do_lists
from backend_main.db_operations.objects.data.composite import \
    upsert_composite as _upsert_composite, view_composite as _view_composite, \
    view_existing_subobject_ids as _view_existing_subobject_ids

from backend_main.domains.objects.general import delete_objects
from backend_main.domains.objects.attributes import ensure_objects_types

from backend_main.util.exceptions import ObjectsNotFound
from backend_main.util.json import error_json

from backend_main.types.request import Request, request_log_event_key
from backend_main.types.domains.objects.attributes import ObjectType
from backend_main.types.domains.objects.data import ObjectIDTypeData


async def upsert_objects_data(request: Request, objects_id_type_and_data: list[ObjectIDTypeData]) -> None:
    try:
        # Upsert links
        links = [o for o in objects_id_type_and_data if o.object_type == "link"]
        if len(links) > 0:
            await ensure_objects_types(request, [o.object_id for o in links], ["link"])
            await _upsert_links(request, links)

        # Upsert markdown
        markdown = [o for o in objects_id_type_and_data if o.object_type == "markdown"]
        if len(markdown) > 0:
            await ensure_objects_types(request, [o.object_id for o in markdown], ["markdown"])
            await _upsert_markdown(request, markdown)

        # Upsert to-do lists
        to_do_lists = [o for o in objects_id_type_and_data if o.object_type == "to_do_list"]
        if len(to_do_lists) > 0:
            await ensure_objects_types(request, [o.object_id for o in to_do_lists], ["to_do_list"])
            await _upsert_to_do_lists(request, to_do_lists)

        # Upsert composite
        composite = [o for o in objects_id_type_and_data if o.object_type == "composite"]
        if len(composite) > 0:
            await ensure_objects_types(request, [o.object_id for o in composite], ["composite"])
            await _upsert_composite(request, composite)

    except ObjectsNotFound as e:
        # Handle attempts to update non-existing objects & objects with incorrect `object_type`
        request[request_log_event_key]("WARNING", "domain", e.msg, e.details)
        raise web.HTTPBadRequest(text=error_json(e.msg), content_type="application/json")


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


async def fully_delete_subobjects(request: Request, subobject_ids: list[int]) -> None:
    """
    Deletes objects with IDs from `subobject_ids`, which are not present in any parent objects.
    """
    if len(subobject_ids) == 0: return
    subobject_ids_set = set(subobject_ids)
    existing_subobject_ids = await _view_existing_subobject_ids(request, subobject_ids_set)
    non_existing_subobject_ids = subobject_ids_set.difference(existing_subobject_ids)
    await delete_objects(request, non_existing_subobject_ids, False)
