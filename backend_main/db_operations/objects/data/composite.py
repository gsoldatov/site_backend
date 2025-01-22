"""
Database operations with composite objects.
"""
from sqlalchemy import select, and_

from backend_main.auth.query_clauses import get_objects_data_auth_filter_clause

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.objects.data import CompositeIDTypeData


async def view_composite(request: Request, object_ids: list[int]) -> list[CompositeIDTypeData]:
    # Handle empty `object_ids`
    if len(object_ids) == 0: return []

    objects = request.config_dict[app_tables_key].objects
    composite = request.config_dict[app_tables_key].composite
    composite_properties = request.config_dict[app_tables_key].composite_properties

    # Query composite properties
    ## Objects filter for non 'admin` user level
    objects_data_auth_filter_clause_items = get_objects_data_auth_filter_clause(request, composite_properties.c.object_id, object_ids)

    rows = await request[request_connection_key].execute(
        select(
            composite_properties.c.object_id,
            composite_properties.c.display_mode,
            composite_properties.c.numerate_chapters
        )
        .select_from(objects.outerjoin(composite_properties, objects.c.object_id == composite_properties.c.object_id))
        .where(and_(
            objects_data_auth_filter_clause_items,
            composite_properties.c.object_id.in_(object_ids)))
    )

    object_data_map = {}
    for r in await rows.fetchall():
        object_data = {**r, "subobjects": []}
        object_id = object_data.pop("object_id")
        object_data_map[object_id] = object_data

    # Query subobjects
    ## Objects filter for non 'admin` user level
    objects_data_auth_filter_clause_items = get_objects_data_auth_filter_clause(request, composite.c.object_id, object_ids)

    rows = await request[request_connection_key].execute(
        select(
            composite.c.object_id,
            composite.c.subobject_id,
            composite.c.row,
            composite.c.column, 
            composite.c.selected_tab,
            composite.c.is_expanded,
            composite.c.show_description_composite,
            composite.c.show_description_as_link_composite
        )
        .where(and_(
            objects_data_auth_filter_clause_items,
            composite.c.object_id.in_(object_ids)))
    )

    for row in await rows.fetchall():
        subobject = {**row}
        object_id = subobject.pop("object_id")
        object_data_map[object_id]["subobjects"].append(subobject)
    
    return [CompositeIDTypeData.model_validate({
        "object_id": object_id,
        "object_type": "composite",
        "object_data": object_data
    }) for object_id, object_data in object_data_map.items()]


async def view_exclusive_subobject_ids(request: Request, object_ids: list[int]) -> list[int]:
    """
    Returns a list of object IDs, which are subobjects only to the objects with specified `object_ids`.
    """
    # Handle empty `object_ids`
    if len(object_ids) == 0: return []
    
    composite = request.config_dict[app_tables_key].composite

    # Get all subobject IDs of deleted subobjects
    result = await request[request_connection_key].execute(
        select(composite.c.subobject_id)
        .distinct()
        .where(composite.c.object_id.in_(object_ids))
    )
    subobjects_of_deleted_objects = set((int(r[0]) for r in await result.fetchall()))

    # Get subobject IDs which are present in other composite objects
    result = await request[request_connection_key].execute(
        select(composite.c.subobject_id)
        .distinct()
        .where(and_(
            composite.c.subobject_id.in_(subobjects_of_deleted_objects),
            composite.c.object_id.notin_(object_ids)
        ))
    )
    subobjects_present_in_other_objects = set((int(r[0]) for r in await result.fetchall()))
    
    # Return subobject IDs which are present only in deleted composite objects
    return [o for o in subobjects_of_deleted_objects if o not in subobjects_present_in_other_objects]
