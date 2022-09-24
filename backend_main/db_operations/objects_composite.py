"""
    Composite object database operations.
"""
from backend_main.util.searchables import add_searchable_updates_for_objects
from aiohttp import web
from sqlalchemy import select
from sqlalchemy.sql import and_

from backend_main.db_operations.auth import get_objects_auth_filter_clause
from backend_main.db_operations.objects import add_objects, update_objects, delete_objects
from backend_main.middlewares.connection import start_transaction

from backend_main.util.json import deserialize_str_to_datetime, error_json
from backend_main.validation.db_operations.object_data import validate_composite
from backend_main.util.object_type_route_handler_resolving import object_type_func_name_mapping, get_object_type_route_handler


async def add_composite(request, obj_ids_and_data):
    return await _add_update_composite(request, obj_ids_and_data)


async def update_composite(request, obj_ids_and_data):
    return await _add_update_composite(request, obj_ids_and_data)


async def view_composite(request, object_ids):
    objects = request.config_dict["tables"]["objects"]
    composite = request.config_dict["tables"]["composite"]
    composite_properties = request.config_dict["tables"]["composite_properties"]

    # Objects filter for non 'admin` user level
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

    # Query subobjects
    records = await request["conn"].execute(    # Return all existing composite objects with provided object ids, including those which don't have any subobjects
        select([objects.c.object_id, composite.c.subobject_id, composite.c.row, composite.c.column, 
            composite.c.selected_tab, composite.c.is_expanded, composite.c.show_description_composite, composite.c.show_description_as_link_composite])
        .select_from(objects.outerjoin(composite, objects.c.object_id == composite.c.object_id))
        .where(and_(
            objects_auth_filter_clause,
            objects.c.object_id.in_(object_ids),
            objects.c.object_type == "composite"))
    )

    subobject_data = {}
    for row in await records.fetchall():
        object_id = row["object_id"]
        subobjects = subobject_data.get(object_id, [])
        if row["subobject_id"] != None: # don't add lines without subobject data
            subobjects.append({
                "object_id": row["subobject_id"],
                "row": row["row"],
                "column": row["column"],
                "selected_tab": row["selected_tab"],
                "is_expanded": row["is_expanded"],
                "show_description_composite": row["show_description_composite"],
                "show_description_as_link_composite": row["show_description_as_link_composite"]
            })
        subobject_data[object_id] = subobjects
    
    # Query composite properties
    records = await request["conn"].execute(
        select([composite_properties.c.object_id, composite_properties.c.display_mode, composite_properties.c.numerate_chapters])
        .select_from(objects.outerjoin(composite_properties, objects.c.object_id == composite_properties.c.object_id))
        .where(and_(
            objects_auth_filter_clause,
            composite_properties.c.object_id.in_(object_ids)))
    )

    composite_properties_data = {
        row["object_id"]: {
            "display_mode": row["display_mode"], 
            "numerate_chapters": row["numerate_chapters"]
        } for row in await records.fetchall()
    }
    
    return [{
        "object_id": object_id, 
        "object_data": {
            "subobjects": subobject_data[object_id],
            "display_mode": composite_properties_data[object_id]["display_mode"],
            "numerate_chapters": composite_properties_data[object_id]["numerate_chapters"]
        }
    } for object_id in subobject_data]
# async def view_composite(request, object_ids):        # TODO delete after testing of new version
#     objects = request.config_dict["tables"]["objects"]
#     composite = request.config_dict["tables"]["composite"]
#     composite_properties = request.config_dict["tables"]["composite_properties"]

#     # Objects filter for non 'admin` user level
#     auth_filter_clause = get_objects_auth_filter_clause(request)

#     # Query subobjects
#     records = await request["conn"].execute(    # Return all existing composite objects with provided object ids, including those which don't have any subobjects
#         select([objects.c.object_id, composite.c.subobject_id, composite.c.row, composite.c.column, 
#             composite.c.selected_tab, composite.c.is_expanded, composite.c.show_description_composite, composite.c.show_description_as_link_composite])
#         .select_from(objects.outerjoin(composite, objects.c.object_id == composite.c.object_id))
#         .where(and_(
#             auth_filter_clause,
#             objects.c.object_id.in_(object_ids),
#             objects.c.object_type == "composite"))
#     )

#     subobject_data = {}
#     for row in await records.fetchall():
#         object_id = row["object_id"]
#         subobjects = subobject_data.get(object_id, [])
#         if row["subobject_id"] != None: # don't add lines without subobject data
#             subobjects.append({
#                 "object_id": row["subobject_id"],
#                 "row": row["row"],
#                 "column": row["column"],
#                 "selected_tab": row["selected_tab"],
#                 "is_expanded": row["is_expanded"],
#                 "show_description_composite": row["show_description_composite"],
#                 "show_description_as_link_composite": row["show_description_as_link_composite"]
#             })
#         subobject_data[object_id] = subobjects
    
#     # Query composite properties
#     records = await request["conn"].execute(
#         select([composite_properties.c.object_id, composite_properties.c.display_mode, composite_properties.c.numerate_chapters])
#         .where(and_(
#             auth_filter_clause,
#             composite_properties.c.object_id.in_(object_ids)))
#     )

#     composite_properties_data = {
#         row["object_id"]: {
#             "display_mode": row["display_mode"], 
#             "numerate_chapters": row["numerate_chapters"]
#         } for row in await records.fetchall()
#     }
    
#     return [{
#         "object_id": object_id, 
#         "object_data": {
#             "subobjects": subobject_data[object_id],
#             "display_mode": composite_properties_data[object_id]["display_mode"],
#             "numerate_chapters": composite_properties_data[object_id]["numerate_chapters"]
#         }
#     } for object_id in subobject_data]


async def _add_update_composite(request, obj_ids_and_data):
    """ Full add/update logic for composite objects with subobject data. """
    _validate(request, obj_ids_and_data)

    # Ensure a transaction is started
    await start_transaction(request)

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
                    "modified_at": request["current_time"],
                    
                    "is_published": so["is_published"],

                    "show_description": so["show_description"],
                    "display_in_feed": so["display_in_feed"],
                    "feed_timestamp": deserialize_str_to_datetime(so["feed_timestamp"], allow_empty_string=True, error_msg=f"Incorrect feed timestamp value for subobject '{so['object_name']}'."),

                    "owner_id": so.get("owner_id", request.user_info.user_id),
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
        
        # Add subobjects as pending for `searchables` update
        add_searchable_updates_for_objects(request, sorted_new_subobject_ids)
    
    request.log_event("INFO", "db_operation", "Added new objects as composite subobjects", details=f"object_ids = {list(id_mapping.values())}")
    return id_mapping


async def _update_existing_subobjects(request, obj_ids_and_data):
    """
    NOTE: check if a transaction is needed if this function is used outside of `_add_update_composite`
    """
    
    # Get existing subobjects' attributes and data
    updated_objects_attributes = []
    updated_ids_and_data = {object_type: [] for object_type in object_type_func_name_mapping}
    
    for obj_id_and_data in obj_ids_and_data:
        data = obj_id_and_data["object_data"]
        for so in data["subobjects"]:
            if so["object_id"] > 0 and "object_type" in so:   # object_type is present only when subobject must be updated
                updated_so_attributes = {
                    "object_id": so["object_id"],
                    "object_name": so["object_name"],
                    "object_description": so["object_description"],
                    "is_published": so["is_published"],
                    "show_description": so["show_description"],
                    "display_in_feed": so["display_in_feed"],
                    "feed_timestamp": deserialize_str_to_datetime(so["feed_timestamp"], allow_empty_string=True, error_msg=f"Incorrect feed timestamp value for subobject '{so['object_name']}'."),
                    "modified_at": request["current_time"]
                }
                if "owner_id" in so:     # don't update owner_id if it was not explicitly passed
                    updated_so_attributes["owner_id"] = so["owner_id"]
                
                updated_objects_attributes.append(updated_so_attributes)

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
        
        # Add subobjects as pending for `searchables` update
        add_searchable_updates_for_objects(request, [so_attr["object_id"] for so_attr in updated_objects_attributes])
        request.log_event("INFO", "db_operation", "Updated existing objects as composite subobjects", details=f"object_ids = {[o['object_id'] for o in updated_objects_attributes]}")


async def _update_composite_properties(request, obj_ids_and_data):
    """ 
    Upserts properties of composite objects into `composite_properties` table.

    NOTE: check if a transaction is needed if this function is used outside of `_add_update_composite`
    """
    composite_properties = request.config_dict["tables"]["composite_properties"]

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
    await request["conn"].execute(
        composite_properties.delete()
        .where(composite_properties.c.object_id.in_(object_ids))
    )

    await request["conn"].execute(
        composite_properties.insert()
        .values(inserted_data)
    )


async def _update_composite_object_data(request, obj_ids_and_data, id_mapping):
    """
    NOTE: check if a transaction is needed if this function is used outside of `_add_update_composite`
    """
    
    objects = request.config_dict["tables"]["objects"]
    composite = request.config_dict["tables"]["composite"]

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
                "selected_tab": so["selected_tab"],
                "is_expanded": so["is_expanded"],
                "show_description_composite": so["show_description_composite"],
                "show_description_as_link_composite": so["show_description_as_link_composite"]
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
        msg = "Subobjects do not exist."
        request.log_event("WARNING", "db_operation", msg, details=f"object_ids = {non_existing_subobject_ids}")
        raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")
    
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
    composite = request.config_dict["tables"]["composite"]

    # Delete marked for full deletion subobjects
    marked_for_full_deletion = set()
    for obj_id_and_data in obj_ids_and_data:
        data = obj_id_and_data["object_data"]
        for so in data["deleted_subobjects"]:
            if so["is_full_delete"]:
                marked_for_full_deletion.add(so["object_id"])
    
    if len(marked_for_full_deletion) > 0:
        # Check which subobjects marked for full deletion are not referenced by other composite objects
        result = await request["conn"].execute(
            select([composite.c.subobject_id])
            .distinct()
            .where(composite.c.subobject_id.in_(marked_for_full_deletion))
        )
        
        non_deletable_ids = set((r[0] for r in await result.fetchall()))
        deletable_ids = list(marked_for_full_deletion.difference(non_deletable_ids))
        
        # Delete subobjects not present in other composite subobjects
        if len(deletable_ids) > 0:
            await delete_objects(request, deletable_ids)
            request.log_event("INFO", "db_operation", "Fully deleted subobjects.", details=f"object_ids = {deletable_ids}")
