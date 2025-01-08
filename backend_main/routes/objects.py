"""
    Object routes.
"""
from aiohttp import web
from jsonschema import validate

from backend_main.validation.schemas.objects import objects_add_schema, objects_update_schema, objects_view_schema, objects_delete_schema,\
    objects_get_page_object_ids_schema, objects_search_schema, objects_update_tags_schema, objects_view_composite_hierarchy_elements_schema
from backend_main.validation.schemas.object_data import link_object_data, markdown_object_data, to_do_list_object_data, composite_object_data

from backend_main.db_operations.objects import add_objects, update_objects, view_objects, view_objects_types, delete_objects,\
    get_page_object_ids_data, search_objects, get_elements_in_composite_hierarchy, set_modified_at
from backend_main.db_operations.objects_tags import update_objects_tags
from backend_main.domains.objects_tags import add_objects_tags, delete_objects_tags, view_objects_tags
from backend_main.middlewares.connection import start_transaction

from backend_main.util.json import deserialize_str_to_datetime, row_proxy_to_dict, error_json
from backend_main.util.object_type_route_handler_resolving import get_object_type_route_handler

from backend_main.types.request import request_time_key, request_log_event_key, request_user_info_key


async def add(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=objects_add_schema)

    # Get and set attribute values
    request_time = request[request_time_key]
    data["object"]["created_at"] = request_time
    data["object"]["modified_at"] = request_time
    data["object"]["feed_timestamp"] = deserialize_str_to_datetime(data["object"]["feed_timestamp"], allow_empty_string=True, error_msg="Incorrect feed timestamp value.")
    added_tags = data["object"].pop("added_tags", [])
    object_data = data["object"].pop("object_data")

    # Set owner_id of the object if it's missing
    data["object"]["owner_id_is_autoset"] = False
    if "owner_id" not in data["object"]:
        data["object"]["owner_id"] = request[request_user_info_key].user_id
        data["object"]["owner_id_is_autoset"] = True
    
    # Start a transaction
    await start_transaction(request)
    
    # Insert general object data
    record = (await add_objects(request, [data["object"]]))[0]
    response_data = row_proxy_to_dict(record)
    object_id = record["object_id"]
    response_data["feed_timestamp"] = response_data["feed_timestamp"] or "" # replace empty feed timestamp with an empty string

    # Call handler to add object-specific data
    specific_data = [{"object_id": object_id, "object_data": object_data}]
    handler = get_object_type_route_handler("add", data["object"]["object_type"])
    returned_object_data = await handler(request, specific_data)
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
    data["object"]["feed_timestamp"] = deserialize_str_to_datetime(data["object"]["feed_timestamp"], allow_empty_string=True, error_msg="Incorrect feed timestamp value.")
    added_tags = data["object"].pop("added_tags", [])
    removed_tag_ids = data["object"].pop("removed_tag_ids", [])
    object_data = data["object"].pop("object_data")

    # Start a transaction
    await start_transaction(request)

    # Update general object data
    object_id = data["object"]["object_id"]
    response_data = row_proxy_to_dict((await update_objects(request, [data["object"]]))[0])
    response_data["feed_timestamp"] = response_data["feed_timestamp"] or "" # replace empty feed timestamp with an empty string

    # Validate object_data property and call handler to update object-specific data
    validate(instance=object_data, schema=get_object_data_update_schema(response_data["object_type"]))
    specific_data = [{"object_id": response_data["object_id"], "object_data": object_data}]
    handler = get_object_type_route_handler("update", response_data["object_type"])
    returned_object_data = await handler(request, specific_data)
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


async def view(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=objects_view_schema)

    # Get object IDs and initialize containers for response data
    object_ids = data.get("object_ids", [])
    object_data_ids = data.get("object_data_ids", [])
    object_attrs, object_data = {}, []

    # Query general attributes and tag IDs for provided object_ids
    if len(object_ids) > 0:
        # Attributes
        for row in await view_objects(request, object_ids):
            object_attrs[row["object_id"]] = row_proxy_to_dict(row)
            object_attrs[row["object_id"]]["feed_timestamp"] = object_attrs[row["object_id"]]["feed_timestamp"] or "" # replace empty feed timestamps with an empty string
            object_attrs[row["object_id"]]["current_tag_ids"] = []
        
        # Tag IDs
        objects_tags = await view_objects_tags(request, object_ids)
        for object_id in object_attrs:
            object_attrs[object_id]["current_tag_ids"] = objects_tags.map[object_id]
        
    # Convert object_attrs to list
    object_attrs = [object_attrs[k] for k in object_attrs]
    
    # Query object data for provided object_data_ids
    if len(object_data_ids) > 0:
        # Query object types for the requested objects
        object_types = await view_objects_types(request, object_data_ids)
        
        # Run handlers for each of the object types
        for object_type in object_types:
            handler = get_object_type_route_handler("view", object_type)

            # handler function must return a list of dict objects with "object_id" and "object_data" keys
            object_type_data = await handler(request, object_data_ids)
            for d in object_type_data:
                d["object_type"] = object_type
            object_data.extend(object_type_data)
    
    if len(object_attrs) == 0 and len(object_data) == 0:
        request[request_log_event_key]("WARNING", "route_handler", "Object IDs are not found or can't be viewed.", details=f"object_ids = {object_ids}, object_data_ids = {object_data_ids}")
        raise web.HTTPNotFound(text=error_json("Objects not found."), content_type="application/json")

    request[request_log_event_key]("INFO", "route_handler", "Returning object attributes and data.", details=f"object_ids = {object_ids}, object_data_ids = {object_data_ids}")
    return {"objects": object_attrs, "object_data": object_data}


async def delete(request):
    # Validate request body
    data = await request.json()
    validate(instance=data, schema=objects_delete_schema)
    object_ids = data["object_ids"]
    delete_subobjects = data.get("delete_subobjects", False)

    # Cascade delete objects and related data
    await delete_objects(request, object_ids, delete_subobjects)

    # Send response
    request[request_log_event_key]("INFO", "route_handler", "Deleted objects.", details=f"object_ids = {object_ids}, delete_subobjects = {delete_subobjects}")
    return {"object_ids": object_ids}


async def get_page_object_ids(request):
    # Validate request data
    data = await request.json()
    validate(instance=data, schema=objects_get_page_object_ids_schema)
    
    result = await get_page_object_ids_data(request, data["pagination_info"])
    request[request_log_event_key]("INFO", "route_handler", "Returning page object IDs.")
    return result


async def search(request):
    # Validate request data
    data = await request.json()
    validate(instance=data, schema=objects_search_schema)

    # Search objects
    object_ids = await search_objects(request, data["query"])

    request[request_log_event_key]("INFO", "route_handler", "Returning object IDs which match search query.")
    return {"object_ids": object_ids}


async def update_tags(request):
    # Perform basic data validation
    data = await request.json()
    validate(instance=data, schema=objects_update_tags_schema)

    # Update objects_tags and send response
    response_data = {}
    # Update tags
    response_data["tag_updates"] = await update_objects_tags(request, data, check_ids=True)
    
    # Set objects' modified_at time
    response_data["modified_at"] = (await set_modified_at(request, data["object_ids"])).isoformat()

    request[request_log_event_key]("INFO", "route_handler", "Updated tags for objects.")
    return response_data


async def view_composite_hierarchy_elements(request):
    # Validate request data
    data = await request.json()
    validate(instance=data, schema=objects_view_composite_hierarchy_elements_schema)

    # Get and return response
    result = await get_elements_in_composite_hierarchy(request, data["object_id"])
    request[request_log_event_key]("INFO", "route_handler", "Returning composite hierarchy.")
    return result
    

def get_object_data_update_schema(object_type):
    return globals()[f"{object_type}_object_data"]


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("/add", add, name="add"),
                    web.put("/update", update, name="update"),
                    web.post("/view", view, name="view"),
                    web.delete("/delete", delete, name="delete"),
                    web.post("/get_page_object_ids", get_page_object_ids, name="get_page_object_ids"),
                    web.post("/search", search, name="search"),
                    web.put("/update_tags", update_tags, name="update_tags"),
                    web.post("/view_composite_hierarchy_elements", view_composite_hierarchy_elements, name="view_composite_hierarchy_elements")
                ])
    return app
