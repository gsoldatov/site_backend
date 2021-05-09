"""
    Composite object database operations.
"""
from aiohttp import web
from sqlalchemy import select
from psycopg2.errors import ForeignKeyViolation

from backend_main.db_operaions.objects import add_objects, update_objects, delete_objects

from backend_main.util.json import error_json
from backend_main.util.validation import validate_composite
from backend_main.util.object_type_route_handler_resolving import object_type_func_name_mapping, get_object_type_route_handler


async def add_composite(request, obj_ids_and_data):
    return await _add_update_composite(request, obj_ids_and_data)


async def update_composite(request, obj_ids_and_data):
    return await _add_update_composite(request, obj_ids_and_data)


async def view_composite(request, object_ids):
    composite = request.app["tables"]["composite"]
    records = await request["conn"].execute(
        select([composite.c.object_id, composite.c.subobject_id, 
                composite.c.row, composite.c.column, composite.c.selected_tab])
        .where(composite.c.object_id.in_(object_ids))
    )

    data = {}
    for row in await records.fetchall():
        object_id = row["object_id"]
        subobjects = data.get(object_id, [])
        subobjects.append({
            "object_id": row["subobject_id"],
            "row": row["row"],
            "column": row["column"],
            "selected_tab": row["selected_tab"]
        })
        data[object_id] = subobjects
    
    return [{ "object_id": object_id, "object_data": { "subobjects": data[object_id] }} for object_id in data]


async def _add_update_composite(request, obj_ids_and_data):
    """ Full add/update logic for composite objects with subobject data. """
    _validate(request, obj_ids_and_data)
    id_mapping = await _add_new_subobjects(request, obj_ids_and_data)
    await _update_existing_subobjects(request, obj_ids_and_data)
    await _update_composite_object_data(request, obj_ids_and_data, id_mapping)
    await _update_existing_subobjects(request, obj_ids_and_data)
    return {"id_mapping": id_mapping}


def _validate(request, obj_ids_and_data):
    # Validate composite object data
    for oid in obj_ids_and_data:
        validate_composite(oid)


async def _add_new_subobjects(request, obj_ids_and_data):
    # Get new subobjects' attributes and data
    new_objects_attributes = {}
    new_data = {object_type: {} for object_type in object_type_func_name_mapping}
    
    for obj_id_and_data in obj_ids_and_data:
        data = obj_id_and_data["object_data"]
        for so in data["subobjects"]:
            subobject_id, object_type = so.get("object_id"), so.get("object_type")
            if subobject_id < 0:
                new_objects_attributes[subobject_id] = {
                    "object_type": object_type,
                    "object_name": so["object_name"],
                    "object_description": so["object_description"],
                    "created_at": request["current_time"],
                    "modified_at": request["current_time"]
                }

                new_data[object_type][subobject_id] = so["object_data"]
    
    id_mapping = {}
    if len(new_objects_attributes) > 0:
        # Sort new objects by their IDs to create a correct old to new ID mapping.
        # Identity should generate new IDs for multiple rows in ascending order for the order they were inserted in:
        # https://stackoverflow.com/questions/50809120/postgres-insert-into-with-select-ordering
        # If it turns out not to be so, then object attributes should be inserted one by one (in add_objects handler).
        sorted_request_subobject_ids = sorted(new_objects_attributes.keys(), reverse=True)
        sorted_new_objects_attributes = [new_objects_attributes[k] for k in sorted_request_subobject_ids]
        
        # Add new objects attributes and data
        added_object_attributes = await add_objects(request, sorted_new_objects_attributes)

        # Map new object IDs from request to actual IDs generated during insert
        sorted_new_subobject_ids = sorted([o["object_id"] for o in added_object_attributes])
        id_mapping = {sorted_request_subobject_ids[i]: sorted_new_subobject_ids[i] for i in range(len(sorted_new_subobject_ids))}

        # Add new objects' data
        for object_type in object_type_func_name_mapping:
            new_object_ids_and_data = []
            object_type_data = new_data[object_type]
            if len(object_type_data) > 0:
                for request_object_id in object_type_data:
                    new_object_ids_and_data.append({
                        "object_id": id_mapping[request_object_id],
                        "object_data": object_type_data[request_object_id]
                    })
            
                handler = get_object_type_route_handler("add", object_type)
                await handler(request, new_object_ids_and_data)
    
    return id_mapping


async def _update_existing_subobjects(request, obj_ids_and_data):    
    # Get existing subobjects' attributes and data
    updated_objects_attributes = []
    updated_ids_and_data = {object_type: [] for object_type in object_type_func_name_mapping}
    
    for obj_id_and_data in obj_ids_and_data:
        data = obj_id_and_data["object_data"]
        for so in data["subobjects"]:
            if so["object_id"] > 0 and so.get("object_type"):   # object_type is present only when subobject must be updated
                updated_objects_attributes.append({
                    "object_id": so["object_id"],
                    "object_name": so["object_name"],
                    "object_description": so["object_description"],
                    "modified_at": request["current_time"]
                })

                updated_ids_and_data[so["object_type"]].append({
                    "object_id": so["object_id"],
                    "object_data": so["object_data"]
                })
    
    if len(updated_objects_attributes) > 0:
        # Update existing subobjects' attributes
        await update_objects(request, updated_objects_attributes)

        # Update existing subobjects' data
        for object_type in object_type_func_name_mapping:
            if len(updated_ids_and_data[object_type]) > 0:
                handler = get_object_type_route_handler("update", object_type)
                await handler(request, updated_ids_and_data[object_type])


async def _update_composite_object_data(request, obj_ids_and_data, id_mapping):
    objects = request.app["tables"]["objects"]
    composite = request.app["tables"]["composite"]

    # Prepare composite object data for insertion
    composite_object_data = []
    for obj_id_and_data in obj_ids_and_data:
        object_id, data = obj_id_and_data["object_id"], obj_id_and_data["object_data"]
        for so in data["subobjects"]:
            composite_object_data.append({
                "object_id": object_id,
                # Map new subobject IDs, but keep existing IDs intact
                "subobject_id": id_mapping.get(so["object_id"], so["object_id"]),
                "row": so["row"],
                "column": so["column"],
                "selected_tab": so["selected_tab"]
            })
    
    # Check if all subobject IDs exist as objects
    new_subobject_ids = [data["subobject_id"] for data in composite_object_data]
    result = await request["conn"].execute(
        select([objects.c.object_id])
        .where(objects.c.object_id.in_(new_subobject_ids))
    )
    existing_subobject_ids = [row[0] for row in await result.fetchall()]
    non_existing_subobject_ids = set(new_subobject_ids).difference(set(existing_subobject_ids))
    if len(non_existing_subobject_ids) > 0:
        raise web.HTTPBadRequest(text=error_json(f"Subobjects with IDs {non_existing_subobject_ids} do not exist."), content_type="application/json")
    
    # Delete existing & insert new composite object data
    object_ids = [obj_id_and_data["object_id"] for obj_id_and_data in obj_ids_and_data]
    await request["conn"].execute(
        composite.delete()
        .where(composite.c.object_id.in_(object_ids))
    )

    await request["conn"].execute(
        composite.insert()
        .values(composite_object_data)
    )


async def _delete_subobjects(request, obj_ids_and_data):
    # Delete marked for full deletion subobjects
    marked_for_full_deletion = set()
    for obj_id_and_data in obj_ids_and_data:
        data = obj_id_and_data["object_data"]
        for so in data["deleted_subobjects"]:
            if so["is_full_delete"]:
                marked_for_full_deletion.set(so["object_id"])
    
    if len(marked_for_full_deletion) > 0:
        # Check which subobjects marked for full deletion are not referenced by other composite objects
        result = await request["conn"].execute(
            select([composite.c.subobject_id])
            .distinct()
            .where(composite.c.subobject_id.in_(marked_for_full_deletion))
        )
        
        non_deletable_ids = set((r[0] for r in await result.fetchall()))
        deletable_ids = marked_for_full_deletion.difference(non_deletable_ids)
        
        # Delete subobjects not present in other composite subobjects
        if len(deletable_ids) > 0:
            await delete_objects(request, deletable_ids)