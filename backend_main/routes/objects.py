"""
Object routes.
"""
from aiohttp import web
from jsonschema import validate

from backend_main.types._jsonschema.schemas.objects import objects_add_schema, objects_update_schema

from backend_main.db_operations.untyped.objects import add_objects as add_objects_untyped, \
    update_objects as update_objects_untyped, add_objects_data as add_objects_data_untyped, \
    update_objects_data as update_objects_data_untyped
from backend_main.domains.objects.attributes import add_objects, update_objects, \
    update_modified_at, view_objects_attributes_and_tags
from backend_main.domains.objects.data import upsert_objects_data, view_objects_data, fully_delete_subobjects
from backend_main.domains.objects.general import view_page_object_ids, search_objects, \
    view_composite_hierarchy, delete_objects, map_objects_ids
from backend_main.domains.objects_tags import add_objects_tags, delete_objects_tags, \
    bulk_add_objects_tags, bulk_delete_objects_tags

from backend_main.util.json import deserialize_str_to_datetime, row_proxy_to_dict, error_json
from backend_main.types._jsonschema.util import validate_object_data

from backend_main.types.app import app_start_transaction_key
from backend_main.types.request import Request, request_time_key, request_log_event_key, request_user_info_key
from backend_main.types.domains.objects.general import CompositeHierarchy
from backend_main.types.domains.objects.attributes import UpsertedObjectAttributes
from backend_main.types.domains.objects.data import objectIDTypeDataAdapter
from backend_main.types.routes.objects import ObjectsBulkUpsertRequestBody, ObjectsBulkUpsertResponseBody, \
    ObjectsViewRequestBody, ObjectsViewResponseBody, \
    ObjectsGetPageObjectIDsRequestBody, ObjectsGetPageObjectIDsResponseBody, \
    ObjectsSearchRequestBody, ObjectsSearchResponseBody, \
    ObjectsUpdateTagsRequestBody, ObjectsUpdateTagsResponseBody, \
    ObjectsViewCompositeHierarchyElementsRequestBody, \
    ObjectsDeleteRequestBody, ObjectsDeleteResponseBody
from backend_main.types.domains.objects_tags import ObjectIDAndAddedTags, ObjectIDAndRemovedTagIDs


async def add(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=objects_add_schema)

    # Get and set attribute values
    request_time = request[request_time_key]
    data["object"]["created_at"] = request_time
    data["object"]["modified_at"] = request_time
    data["object"]["feed_timestamp"] = deserialize_str_to_datetime(data["object"]["feed_timestamp"], allow_none=True, error_msg="Incorrect feed timestamp value.")
    object_type = data["object"]["object_type"]
    added_tags = data["object"].pop("added_tags", [])
    object_data = data["object"].pop("object_data")

    # Set owner_id of the object if it's missing
    data["object"]["owner_id_is_autoset"] = False
    if "owner_id" not in data["object"]:
        data["object"]["owner_id"] = request[request_user_info_key].user_id
        data["object"]["owner_id_is_autoset"] = True
    
    # Start a transaction
    await request.config_dict[app_start_transaction_key](request)
    
    # Insert general object data
    record = (await add_objects_untyped(request, [data["object"]]))[0]
    response_data = row_proxy_to_dict(record)
    object_id = record["object_id"]
    
    # Call handler to add object-specific data
    obj_ids_and_data = [{"object_id": object_id, "object_data": object_data}]
    returned_object_data = await add_objects_data_untyped(request, object_type, obj_ids_and_data)
    if returned_object_data != None:
        response_data["object_data"] = returned_object_data

    # Set tags of the new object
    added_objects_tags = await add_objects_tags(request, [object_id], added_tags)
    response_data["tag_updates"] = {"added_tag_ids": added_objects_tags.tag_ids, "removed_tag_ids": []}

    # Send response with object's general data; object-specific data is kept on the frontend and displayed after receiving the response or retrived via object
    request[request_log_event_key]("INFO", "route_handler", f"Finished adding object.", details=f"object_id = {object_id}.")
    return {"object": response_data}


async def update(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=objects_update_schema)

    # Get and set attribute values
    request_time = request[request_time_key]
    data["object"]["modified_at"] = request_time
    data["object"]["feed_timestamp"] = deserialize_str_to_datetime(data["object"]["feed_timestamp"], allow_none=True, error_msg="Incorrect feed timestamp value.")
    added_tags = data["object"].pop("added_tags", [])
    removed_tag_ids = data["object"].pop("removed_tag_ids", [])
    object_data = data["object"].pop("object_data")

    # Start a transaction
    await request.config_dict[app_start_transaction_key](request)

    # Update general object data
    object_id = data["object"]["object_id"]
    response_data = row_proxy_to_dict((await update_objects_untyped(request, [data["object"]]))[0])

    # Validate object_data property and call handler to update object-specific data
    object_type = response_data["object_type"]
    validate_object_data(object_type, object_data)
    obj_ids_and_data = [{"object_id": object_id, "object_data": object_data}]
    returned_object_data = await update_objects_data_untyped(request, object_type, obj_ids_and_data)
    if returned_object_data != None:
        response_data["object_data"] = returned_object_data
    
    # Update object's tags
    added_objects_tags = await add_objects_tags(request, [object_id], added_tags)
    removed_objects_tags = await delete_objects_tags(request, [object_id], removed_tag_ids)
    response_data["tag_updates"] = {
        "added_tag_ids": added_objects_tags.tag_ids, 
        "removed_tag_ids": removed_objects_tags.tag_ids
    }

    # Send response with object's general data; object-specific data is kept on the frontend and displayed after receiving the response or retrived via object
    request[request_log_event_key]("INFO", "route_handler", f"Finished updating object.", details=f"object_id = {object_id}.")
    return {"object": response_data}


async def bulk_upsert(request: Request) -> ObjectsBulkUpsertResponseBody:
    # Validate request data
    data = ObjectsBulkUpsertRequestBody.model_validate(await request.json())
    request_time = request[request_time_key]

    # Start a transaction
    await request.config_dict[app_start_transaction_key](request)

    # Add new objects' attributes
    upserted_objects_attributes = [UpsertedObjectAttributes.model_validate({
        **o.model_dump(), "created_at": request_time, "modified_at": request_time,
    }) for o in data.objects]

    new_objects_attributes = [o for o in upserted_objects_attributes if o.object_id <= 0]
    objects_ids_map = await add_objects(request, new_objects_attributes)

    # Update existing objects' attributes
    existing_objects_attributes = [o for o in upserted_objects_attributes if o.object_id > 0]
    await update_objects(request, existing_objects_attributes)

    # Map IDs of new objects & subobjects
    mapped_objects = map_objects_ids(data.objects, objects_ids_map)

    # Update objects tags
    objects_ids_and_added_tags = [ObjectIDAndAddedTags.model_validate(o, from_attributes=True) for o in mapped_objects]
    await bulk_add_objects_tags(request, objects_ids_and_added_tags)
    objects_ids_and_removed_tag_ids = [ObjectIDAndRemovedTagIDs.model_validate(o, from_attributes=True) for o in mapped_objects]
    await bulk_delete_objects_tags(request, objects_ids_and_removed_tag_ids)

    # Update objects data
    objects_id_type_and_data = [objectIDTypeDataAdapter.validate_python(o, from_attributes=True) for o in mapped_objects]
    await upsert_objects_data(request, objects_id_type_and_data)    

    # Delete subobjects marked as fully deleted
    # (NOTE: this is done after composite object data is updated, because
    # domain function does not check, if parent IDs belong to the upserted objects
    # (which should be excluded from the check))
    #
    # Object IDs, added during the request, are filtered from full deletion
    fully_deleted_subobject_ids = list(
        set(data.fully_deleted_subobject_ids).difference(set(objects_ids_map.map.values()))
    )
    await fully_delete_subobjects(request, fully_deleted_subobject_ids)

    # View upserts objects attributes, tags & data and return them
    object_ids = list(o.object_id for o in mapped_objects)
    objects_attributes_and_tags = await view_objects_attributes_and_tags(request, object_ids)
    objects_data = await view_objects_data(request, object_ids)
    request[request_log_event_key]("INFO", "route_handler", f"Finished upserting objects.", details=f"object_ids = {object_ids}.")
    return ObjectsViewResponseBody(
        objects_attributes_and_tags=objects_attributes_and_tags,
        objects_data=objects_data
    )


async def update_tags(request: Request) -> ObjectsUpdateTagsResponseBody:
    # Validate request data
    data = ObjectsUpdateTagsRequestBody.model_validate(await request.json())

    # Start a transaction
    await request.config_dict[app_start_transaction_key](request)

    # Update tags and objects `modified_at` attribute
    added_objects_tags = await add_objects_tags(request, data.object_ids, data.added_tags)
    removed_objects_tags = await delete_objects_tags(request, data.object_ids, data.removed_tag_ids)
    modified_at = await update_modified_at(request, data.object_ids, request[request_time_key])

    # Log and return response
    response = ObjectsUpdateTagsResponseBody.model_validate({
        "tag_updates": {
            "added_tag_ids": added_objects_tags.tag_ids,
            "removed_tag_ids": removed_objects_tags.tag_ids
        },        
        "modified_at": modified_at
    })

    request[request_log_event_key]("INFO", "route_handler", "Updated tags for objects.")
    return response


async def view(request: Request) -> ObjectsViewResponseBody:
    # Validate request body
    data = ObjectsViewRequestBody.model_validate(await request.json())

    # Query attributes and tags
    objects_attributes_and_tags = await view_objects_attributes_and_tags(request, data.object_ids)

    # Query data
    objects_data = await view_objects_data(request, data.object_data_ids)

    # Handle no data found case & return response
    if len(objects_attributes_and_tags) == 0 and len(objects_data) == 0:
        request[request_log_event_key](
            "WARNING", "route_handler", "Object IDs are not found or can't be viewed.",
            details=f"object_ids = {data.object_ids}, object_data_ids = {data.object_data_ids}"
        )
        raise web.HTTPNotFound(text=error_json("Objects not found."), content_type="application/json")

    request[request_log_event_key](
        "INFO", "route_handler", "Returning object attributes and data.",
        details=f"object_ids = {data.object_ids}, object_data_ids = {data.object_data_ids}"
    )
    return ObjectsViewResponseBody(
        objects_attributes_and_tags=objects_attributes_and_tags,
        objects_data=objects_data
    )


async def get_page_object_ids(request: Request) -> ObjectsGetPageObjectIDsResponseBody:
    # Validate request data
    data = ObjectsGetPageObjectIDsRequestBody.model_validate(await request.json())

    # Get page object IDs, log and send response
    result = await view_page_object_ids(request, data.pagination_info)
    request[request_log_event_key]("INFO", "route_handler", "Returning page object IDs.")
    return ObjectsGetPageObjectIDsResponseBody(pagination_info=result)


async def search(request: Request) -> ObjectsSearchResponseBody:
    # Validate request data
    data = ObjectsSearchRequestBody.model_validate(await request.json())

    # Search objects
    object_ids = await search_objects(request, data.query)

    request[request_log_event_key]("INFO", "route_handler", "Returning object IDs which match search query.")
    return ObjectsSearchResponseBody(object_ids=object_ids)


async def view_composite_hierarchy_elements(request: Request) -> CompositeHierarchy:
    # Validate request data
    data = ObjectsViewCompositeHierarchyElementsRequestBody.model_validate(await request.json())

    # Get and return response
    result = await view_composite_hierarchy(request, data.object_id)
    request[request_log_event_key]("INFO", "route_handler", "Returning composite hierarchy.")
    return result


async def delete(request: Request) -> ObjectsDeleteResponseBody:
    # Validate request body
    data = ObjectsDeleteRequestBody.model_validate(await request.json())

    # Delete objects, log and send response
    await delete_objects(request, data.object_ids, data.delete_subobjects)
    request[request_log_event_key](
        "INFO", "route_handler", "Deleted objects.", 
        details=f"object_ids = {data.object_ids}, delete_subobjects = {data.delete_subobjects}"
    )
    return ObjectsDeleteResponseBody(object_ids=data.object_ids)


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("/add", add, name="add"),
                    web.put("/update", update, name="update"),
                    web.post("/bulk_upsert", bulk_upsert, name="bulk_upsert"),
                    web.put("/update_tags", update_tags, name="update_tags"),
                    web.post("/view", view, name="view"),
                    web.post("/get_page_object_ids", get_page_object_ids, name="get_page_object_ids"),
                    web.post("/search", search, name="search"),
                    web.post("/view_composite_hierarchy_elements", view_composite_hierarchy_elements, name="view_composite_hierarchy_elements"),                    
                    web.delete("/delete", delete, name="delete")
                ])
    return app
