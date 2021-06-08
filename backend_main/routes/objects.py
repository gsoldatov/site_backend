"""
    Object routes.
"""
from datetime import datetime

from aiohttp import web
from jsonschema import validate

from backend_main.schemas.objects import objects_add_schema, objects_update_schema, objects_view_schema, objects_delete_schema,\
    objects_get_page_object_ids_schema, objects_search_schema, objects_update_tags_schema
from backend_main.schemas.object_data import link_object_data, markdown_object_data, to_do_list_object_data, composite_object_data

from backend_main.db_operaions.objects import add_objects, update_objects, view_objects, view_objects_types, delete_objects,\
    get_page_object_ids_data, search_objects, set_modified_at
from backend_main.db_operaions.objects_tags import view_objects_tags, update_objects_tags

from backend_main.util.json import row_proxy_to_dict, error_json, serialize_datetime_to_str
from backend_main.util.object_type_route_handler_resolving import get_object_type_route_handler


async def add(request):
    # Validate request body
    data = await request.json()
    validate(instance = data, schema = objects_add_schema)

    # Get and set attribute values
    current_time = datetime.utcnow()
    request["current_time"] = current_time
    data["object"]["created_at"] = current_time
    data["object"]["modified_at"] = current_time
    added_tags = data["object"].pop("added_tags", [])
    object_data = data["object"].pop("object_data")
    
    # Insert general object data
    record = (await add_objects(request, [data["object"]]))[0]
    response_data = row_proxy_to_dict(record)
    object_id = record["object_id"]

    # Call handler to add object-specific data
    specific_data = [{"object_id": object_id, "object_data": object_data}]
    handler = get_object_type_route_handler("add", data["object"]["object_type"])
    returned_object_data = await handler(request, specific_data)
    if returned_object_data != None:
        response_data["object_data"] = returned_object_data

    # Set tags of the new object
    response_data["tag_updates"] = await update_objects_tags(request, {"object_ids": [object_id], "added_tags": added_tags})

    # Send response with object's general data; object-specific data is kept on the frontend and displayed after receiving the response or retrived via object
    return web.json_response({"object": response_data})


async def update(request):
    # Validate request body
    data = await request.json()
    validate(instance = data, schema = objects_update_schema)

    # Get and set attribute values
    current_time = datetime.utcnow()
    request["current_time"] = current_time
    data["object"]["modified_at"] = current_time
    added_tags = data["object"].pop("added_tags", [])
    removed_tag_ids = data["object"].pop("removed_tag_ids", [])
    object_data = data["object"].pop("object_data")

    # Update general object data
    object_id = data["object"]["object_id"]
    response_data = row_proxy_to_dict((await update_objects(request, [data["object"]]))[0])

    # Validate object_data property and call handler to update object-specific data
    validate(instance = object_data, schema = get_object_data_update_schema(response_data["object_type"]))
    specific_data = [{"object_id": response_data["object_id"], "object_data": object_data}]
    handler = get_object_type_route_handler("update", response_data["object_type"])
    returned_object_data = await handler(request, specific_data)
    if returned_object_data != None:
        response_data["object_data"] = returned_object_data
    
    # Update object's tags
    response_data["tag_updates"] = await update_objects_tags(request, 
        {"object_ids": [object_id], "added_tags": added_tags, "removed_tag_ids": removed_tag_ids})

    # Send response with object's general data; object-specific data is kept on the frontend and displayed after receiving the response or retrived via object
    return web.json_response({"object": response_data})


async def view(request):
    # Validate request body
    data = await request.json()
    validate(instance = data, schema = objects_view_schema)

    # Get object IDs and initialize containers for response data
    object_ids = data.get("object_ids", [])
    object_data_ids = data.get("object_data_ids", [])
    object_attrs, object_data = {}, []

    # Query general attributes and tag IDs for provided object_ids
    if len(object_ids) > 0:
        # Attributes
        for row in await view_objects(request, object_ids):
            object_attrs[row["object_id"]] = row_proxy_to_dict(row)
            object_attrs[row["object_id"]]["current_tag_ids"] = []
        
        # Tag IDs
        for row in await view_objects_tags(request, object_ids = object_ids):
            object_attrs[row["object_id"]]["current_tag_ids"].append(row["tag_id"])
        
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
        raise web.HTTPNotFound(text = error_json("Objects not found."), content_type = "application/json")

    return web.json_response({ "objects": object_attrs, "object_data": object_data })


async def delete(request):
    # Validate request body
    data = await request.json()
    validate(instance = data, schema = objects_delete_schema)
    object_ids = data["object_ids"]
    delete_subobjects = data.get("delete_subobjects", False)

    # Cascade delete objects and related data
    await delete_objects(request, object_ids, delete_subobjects)

    # Send response
    return web.json_response({"object_ids": object_ids})


async def get_page_object_ids(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = objects_get_page_object_ids_schema)
    
    return web.json_response(await get_page_object_ids_data(request, data["pagination_info"]))


async def search(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = objects_search_schema)

    # Search objects
    object_ids = await search_objects(request, data["query"])

    return web.json_response({"object_ids": object_ids})


async def update_tags(request):
    # Perform basic data validation
    data = await request.json()
    validate(instance = data, schema = objects_update_tags_schema)

    # Update objects_tags and send response
    response_data = {}
    # Update tags
    response_data["tag_updates"] = await update_objects_tags(request, data, check_ids = True)
    
    # Set objects' modified_at time
    response_data["modified_at"] = serialize_datetime_to_str(await set_modified_at(request, data["object_ids"]))

    return web.json_response(response_data)


def get_object_data_update_schema(object_type):
    return globals()[f"{object_type}_object_data"]


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("/add", add, name = "add"),
                    web.put("/update", update, name = "update"),
                    web.post("/view", view, name = "view"),
                    web.delete("/delete", delete, name = "delete"),
                    web.post("/get_page_object_ids", get_page_object_ids, name = "get_page_object_ids"),
                    web.post("/search", search, name = "search"),
                    web.put("/update_tags", update_tags, name = "update_tags"),
                ])
    return app
