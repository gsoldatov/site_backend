"""
    Composite object database operations.
"""
from backend_main.util.searchables import add_searchable_updates_for_objects
from aiohttp import web
from sqlalchemy import select

from backend_main.db_operations.untyped.objects import add_objects, update_objects, add_objects_data, update_objects_data
from backend_main.domains.objects.general import delete_objects

from backend_main.util.json import deserialize_str_to_datetime, error_json
from backend_main.types._jsonschema.db_operations.object_data import validate_composite

from backend_main.types.app import app_tables_key
from backend_main.types.request import request_time_key, request_log_event_key, request_user_info_key, request_connection_key


_OBJECT_TYPES_WITHOUT_COMPOSITE = ("link", "markdown", "to_do_list")


async def add_composite(request, obj_ids_and_data):
    return await _add_update_composite(request, obj_ids_and_data)


async def update_composite(request, obj_ids_and_data):
    return await _add_update_composite(request, obj_ids_and_data)


async def _add_update_composite(request, obj_ids_and_data):
    """ Full add/update logic for composite objects with subobject data. """
    _validate(request, obj_ids_and_data)

    id_mapping = await _add_new_subobjects(request, obj_ids_and_data)
    await _update_existing_subobjects(request, obj_ids_and_data)
    await _update_composite_properties(request, obj_ids_and_data)
    await _update_composite_object_data(request, obj_ids_and_data, id_mapping)
    # await _update_existing_subobjects(request, obj_ids_and_data)    # was called a second time for unknown reasons
    await _delete_subobjects(request, obj_ids_and_data)
    return {"id_mapping": id_mapping}


def _validate(request, obj_ids_and_data):
    # Validate composite object data
    for oid in obj_ids_and_data:
        validate_composite(oid)


async def _add_new_subobjects(request, obj_ids_and_data):
    """
    NOTE: check if a transaction is needed if this function is used outside of `_add_update_composite`
    """
    request_time = request[request_time_key]

    # Get new subobjects' attributes and data
    new_objects_attributes = {}
    new_data = {object_type: {} for object_type in ("link", "markdown", "to_do_list")}
    
    for obj_id_and_data in obj_ids_and_data:
        data = obj_id_and_data["object_data"]
        for so in data["subobjects"]:
            subobject_id, object_type = so.get("subobject_id"), so.get("object_type")

            if subobject_id < 0:
                new_objects_attributes[subobject_id] = {
                    "object_type": object_type,
                    "object_name": so["object_name"],
                    "object_description": so["object_description"],
                    "created_at": request_time,
                    "modified_at": request_time,
                    
                    "is_published": so["is_published"],

                    "show_description": so["show_description"],
                    "display_in_feed": so["display_in_feed"],
                    "feed_timestamp": deserialize_str_to_datetime(so["feed_timestamp"], allow_none=True, error_msg=f"Incorrect feed timestamp value for subobject '{so['object_name']}'."),

                    "owner_id": so.get("owner_id", request[request_user_info_key].user_id),
                    "owner_id_is_autoset": not ("owner_id" in so)
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
        for object_type in _OBJECT_TYPES_WITHOUT_COMPOSITE:
            new_object_ids_and_data = []
            object_type_data = new_data[object_type]
            if len(object_type_data) > 0:
                for request_subobject_id in object_type_data:
                    new_object_ids_and_data.append({
                        "object_id": id_mapping[request_subobject_id],
                        "object_data": object_type_data[request_subobject_id]
                    })
                await add_objects_data(request, object_type, new_object_ids_and_data)
        
        # Add subobjects as pending for `searchables` update
        add_searchable_updates_for_objects(request, sorted_new_subobject_ids)
    
    request[request_log_event_key]("INFO", "db_operation", "Added new objects as composite subobjects",
                                   details={"object_ids": list(id_mapping.values())})
    return id_mapping


async def _update_existing_subobjects(request, obj_ids_and_data):
    """
    NOTE: check if a transaction is needed if this function is used outside of `_add_update_composite`
    """
    request_time = request[request_time_key]
    
    # Get existing subobjects' attributes and data
    updated_objects_attributes = []
    updated_ids_and_data = {object_type: [] for object_type in _OBJECT_TYPES_WITHOUT_COMPOSITE}
    
    for obj_id_and_data in obj_ids_and_data:
        data = obj_id_and_data["object_data"]
        for so in data["subobjects"]:
            if so["subobject_id"] > 0 and "object_type" in so:   # object_type is present only when subobject must be updated
                updated_so_attributes = {
                    "object_id": so["subobject_id"],
                    "object_name": so["object_name"],
                    "object_description": so["object_description"],
                    "is_published": so["is_published"],
                    "show_description": so["show_description"],
                    "display_in_feed": so["display_in_feed"],
                    "feed_timestamp": deserialize_str_to_datetime(so["feed_timestamp"], allow_none=True, error_msg=f"Incorrect feed timestamp value for subobject '{so['object_name']}'."),
                    "modified_at": request_time
                }
                if "owner_id" in so:     # don't update owner_id if it was not explicitly passed
                    updated_so_attributes["owner_id"] = so["owner_id"]
                
                updated_objects_attributes.append(updated_so_attributes)

                updated_ids_and_data[so["object_type"]].append({
                    "object_id": so["subobject_id"],
                    "object_data": so["object_data"]
                })
    
    if len(updated_objects_attributes) > 0:
        # Update existing subobjects' attributes
        await update_objects(request, updated_objects_attributes)

        # Update existing subobjects' data
        for object_type in _OBJECT_TYPES_WITHOUT_COMPOSITE:
            if len(updated_ids_and_data[object_type]) > 0:
                await update_objects_data(request, object_type, updated_ids_and_data[object_type])
        
        # Add subobjects as pending for `searchables` update
        add_searchable_updates_for_objects(request, [so_attr["object_id"] for so_attr in updated_objects_attributes])
        request[request_log_event_key]("INFO", "db_operation", "Updated existing objects as composite subobjects",
                                       details={"object_ids": [o['object_id'] for o in updated_objects_attributes]})


async def _update_composite_properties(request, obj_ids_and_data):
    """ 
    Upserts properties of composite objects into `composite_properties` table.

    NOTE: check if a transaction is needed if this function is used outside of `_add_update_composite`
    """
    composite_properties = request.config_dict[app_tables_key].composite_properties

    # Prepare data for insertion
    inserted_data = []
    for obj_id_and_data in obj_ids_and_data:
        object_id, data = obj_id_and_data["object_id"], obj_id_and_data["object_data"]
        inserted_data.append({
            "object_id": object_id,
            "display_mode": data["display_mode"],
            "numerate_chapters": data["numerate_chapters"]
        })
    
    # Delete existing & insert new composite object data
    object_ids = [obj_id_and_data["object_id"] for obj_id_and_data in obj_ids_and_data]
    await request[request_connection_key].execute(
        composite_properties.delete()
        .where(composite_properties.c.object_id.in_(object_ids))
    )

    await request[request_connection_key].execute(
        composite_properties.insert()
        .values(inserted_data)
    )


async def _update_composite_object_data(request, obj_ids_and_data, id_mapping):
    """
    NOTE: check if a transaction is needed if this function is used outside of `_add_update_composite`
    """
    objects = request.config_dict[app_tables_key].objects
    composite = request.config_dict[app_tables_key].composite

    # Prepare composite object data for insertion
    composite_object_data = []
    for obj_id_and_data in obj_ids_and_data:
        object_id, data = obj_id_and_data["object_id"], obj_id_and_data["object_data"]
        for so in data["subobjects"]:
            composite_object_data.append({
                "object_id": object_id,
                # Map new subobject IDs, but keep existing IDs intact
                "subobject_id": id_mapping.get(so["subobject_id"], so["subobject_id"]),
                "row": so["row"],
                "column": so["column"],
                "selected_tab": so["selected_tab"],
                "is_expanded": so["is_expanded"],
                "show_description_composite": so["show_description_composite"],
                "show_description_as_link_composite": so["show_description_as_link_composite"]
            })
    
    # Check if all subobject IDs exist as objects
    new_subobject_ids = [data["subobject_id"] for data in composite_object_data]
    result = await request[request_connection_key].execute(
        select(objects.c.object_id)
        .where(objects.c.object_id.in_(new_subobject_ids))
    )
    existing_subobject_ids = [row[0] for row in await result.fetchall()]
    non_existing_subobject_ids = list(set(new_subobject_ids).difference(set(existing_subobject_ids)))
    if len(non_existing_subobject_ids) > 0:
        msg = "Subobjects do not exist."
        request[request_log_event_key]("WARNING", "db_operation", msg, details={"object_ids": non_existing_subobject_ids})
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")
    
    # Delete existing & insert new composite object data
    object_ids = [obj_id_and_data["object_id"] for obj_id_and_data in obj_ids_and_data]
    await request[request_connection_key].execute(
        composite.delete()
        .where(composite.c.object_id.in_(object_ids))
    )

    await request[request_connection_key].execute(
        composite.insert()
        .values(composite_object_data)
    )


async def _delete_subobjects(request, obj_ids_and_data):
    composite = request.config_dict[app_tables_key].composite

    # Delete marked for full deletion subobjects
    marked_for_full_deletion = set()
    for obj_id_and_data in obj_ids_and_data:
        data = obj_id_and_data["object_data"]
        for so in data["deleted_subobjects"]:
            if so["is_full_delete"]:
                marked_for_full_deletion.add(so["object_id"])
    
    if len(marked_for_full_deletion) > 0:
        # Check which subobjects marked for full deletion are not referenced by other composite objects
        result = await request[request_connection_key].execute(
            select(composite.c.subobject_id)
            .distinct()
            .where(composite.c.subobject_id.in_(marked_for_full_deletion))
        )
        
        non_deletable_ids = set((r[0] for r in await result.fetchall()))
        deletable_ids = list(marked_for_full_deletion.difference(non_deletable_ids))
        
        # Delete subobjects not present in other composite subobjects
        if len(deletable_ids) > 0:
            await delete_objects(request, deletable_ids, False)
            request[request_log_event_key]("INFO", "db_operation", "Fully deleted subobjects.", details={"object_ids": deletable_ids})
