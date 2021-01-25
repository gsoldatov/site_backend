"""
    Object routes.
"""
from datetime import datetime

from aiohttp import web
from jsonschema import validate
from sqlalchemy import select, func
from sqlalchemy.sql import and_

from backend_main.schemas.objects import objects_add_schema, objects_update_schema, objects_view_schema, objects_delete_schema,\
    objects_get_page_object_ids_schema, objects_search_schema, objects_update_tags_schema, object_types_enum
from backend_main.schemas.object_data import link_object_data, markdown_object_data, to_do_list_object_data

from backend_main.db_operaions.objects_links import add_link, view_link, update_link, delete_link
from backend_main.db_operaions.objects_markdown import add_markdown, view_markdown, update_markdown, delete_markdown
from backend_main.db_operaions.objects_tags import update_objects_tags
from backend_main.db_operaions.objects import set_modified_at

from backend_main.util.json import row_proxy_to_dict, error_json


async def add(request):
    # Validate request body
    data = await request.json()
    validate(instance = data, schema = objects_add_schema)
    current_time = datetime.utcnow()
    data["object"]["created_at"] = current_time
    data["object"]["modified_at"] = current_time
    added_tags = data["object"].pop("added_tags", [])

    conn = request["conn"]
    object_data = data["object"].pop("object_data")

    # Insert general object data
    objects = request.app["tables"]["objects"]
    
    result = await conn.execute(objects.insert()
        .returning(objects.c.object_id, objects.c.object_type, objects.c.created_at, objects.c.modified_at,
                objects.c.object_name, objects.c.object_description)
        .values(data["object"])
        )
    record = await result.fetchone()
    response_data = row_proxy_to_dict(record)
    object_id = record["object_id"]

    # Call handler to add object-specific data
    specific_data = {"object_id": object_id, "object_data": object_data}
    handler = get_func_name("add", data["object"]["object_type"])
    await handler(request, specific_data)

    # Set tags of the new object
    response_data["tag_updates"] = await update_objects_tags(request, {"object_ids": [object_id], "added_tags": added_tags})

    # Send response with object's general data; object-specific data is kept on the frontend and displayed after receiving the response or retrived via object
    return web.json_response({"object": response_data})


async def view(request):
    # Validate request body
    data = await request.json()
    validate(instance = data, schema = objects_view_schema)

    conn = request["conn"]
    objects = request.app["tables"]["objects"]
    objects_tags = request.app["tables"]["objects_tags"]
    object_ids = data.get("object_ids", [])
    object_data_ids = data.get("object_data_ids", [])
    object_attrs, object_data = {}, []

    # Query general attributes and tag IDs for provided object_ids
    if len(object_ids) > 0:
        # Attributes
        object_attrs_result = await conn.execute(select([objects.c.object_id, objects.c.object_type, objects.c.created_at,
                                            objects.c.modified_at, objects.c.object_name, objects.c.object_description])
                                    .where(objects.c.object_id.in_(object_ids))
        )

        for row in await object_attrs_result.fetchall():
            object_attrs[row["object_id"]] = row_proxy_to_dict(row)
            object_attrs[row["object_id"]]["current_tag_ids"] = []
        
        # Tag IDs
        objects_tags_result = await conn.execute(select([objects_tags.c.object_id, objects_tags.c.tag_id])
                                                .where(objects_tags.c.object_id.in_(object_ids))
        )
        for row in await objects_tags_result.fetchall():
            object_attrs[row["object_id"]]["current_tag_ids"].append(row["tag_id"])
        
        # Convert object_attrs to list
        object_attrs = [object_attrs[k] for k in object_attrs]
    
    # Query object data for provided object_data_ids
    if len(object_data_ids) > 0:
        # Query object types for the requested objects
        result = await conn.execute(select([objects.c.object_type])
                                    .distinct()
                                    .where(objects.c.object_id.in_(object_data_ids))
        )
        object_types = []
        for row in await result.fetchall():
            object_types.append(row["object_type"])
        
        # Run handlers for each of the object types
        for object_type in object_types:
            handler = get_func_name("view", object_type)

            # handler function must return a list of dict objects with specific object_data attributes
            object_type_data = await handler(request, object_data_ids)
            for d in object_type_data:
                d["object_type"] = object_type
            object_data.extend(object_type_data)
    
    if len(object_attrs) == 0 and len(object_data) == 0:
        raise web.HTTPNotFound(text = error_json("Objects not found."), content_type = "application/json")

    return web.json_response({ "objects": object_attrs, "object_data": object_data })


async def update(request):
    # Validate request body
    data = await request.json()
    validate(instance = data, schema = objects_update_schema)
    current_time = datetime.utcnow()
    data["object"]["modified_at"] = current_time
    added_tags = data["object"].pop("added_tags", [])
    removed_tag_ids = data["object"].pop("removed_tag_ids", [])

    # Insert general object data
    conn = request["conn"]
    object_data = data["object"].pop("object_data")

    # Insert general object data
    objects = request.app["tables"]["objects"]
    object_id = data["object"]["object_id"]
    
    result = await conn.execute(objects.update()
        .where(objects.c.object_id == object_id)
        .values(data["object"])
        .returning(objects.c.object_id, objects.c.object_type, objects.c.created_at, objects.c.modified_at,
                objects.c.object_name, objects.c.object_description)
        )
    record = await result.fetchone()
    if not record:
        raise web.HTTPNotFound(text = error_json(f"object_id '{object_id}' not found."), content_type = "application/json")
    response_data = row_proxy_to_dict(record)

    # Validate object_data property and call handler to update object-specific data
    validate(instance = object_data, schema = get_object_data_update_schema(record["object_type"]))
    specific_data = {"object_id": record["object_id"], "object_data": object_data}
    handler = get_func_name("update", record["object_type"])
    await handler(request, specific_data)
    
    # Update object's tags
    response_data["tag_updates"] = await update_objects_tags(request, 
        {"object_ids": [object_id], "added_tags": added_tags, "removed_tag_ids": removed_tag_ids})

    # Send response with object's general data; object-specific data is kept on the frontend and displayed after receiving the response or retrived via object
    return web.json_response({"object": response_data})


async def delete(request):
    # Validate request body
    data = await request.json()
    validate(instance = data, schema = objects_delete_schema)

    conn = request["conn"]
    object_ids = data["object_ids"]
        
    # Remove objects' tags
    await update_objects_tags(request, {"object_ids": object_ids, "remove_all_tags": True})

    # Get object types and call handlers for each type to delete object-specific data
    objects = request.app["tables"]["objects"]
    result = await conn.execute(select([objects.c.object_type])
                .distinct()
                .where(objects.c.object_id.in_(object_ids))
                )
    object_types = []
    for row in await result.fetchall():
        object_types.append(row["object_type"])

    if len(object_types) == 0:
        raise web.HTTPNotFound(text = error_json("Objects(s) not found."), content_type = "application/json")

    for object_type in object_types:
        handler = get_func_name("delete", object_type)
        await handler(request, object_ids)

    # Delete general data
    result = await conn.execute(objects.delete()
                .where(objects.c.object_id.in_(object_ids))
                .returning(objects.c.object_id)
                )
    object_ids = []
    for row in await result.fetchall():
        object_ids.append(row["object_id"])

    # Send response
    response = {"object_ids": object_ids}
    return web.json_response(response)


async def get_page_object_ids(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = objects_get_page_object_ids_schema)

    # Set query params
    conn = request["conn"]
    objects = request.app["tables"]["objects"]
    objects_tags = request.app["tables"]["objects_tags"]
    p = data["pagination_info"]
    order_by = objects.c.modified_at if p["order_by"] == "modified_at" else objects.c.object_name
    order_asc = p["sort_order"] == "asc"
    items_per_page = p["items_per_page"]
    first = (p["page"] - 1) * items_per_page
    filter_text = f"%{p['filter_text'].lower()}%"
    object_types = p["object_types"] if len(p["object_types"]) > 0 else object_types_enum
    tags_filter = p["tags_filter"]

    # Sub-query for filtering objects which match tags filter condition
    tags_filter_subquery = (
        select([objects_tags.c.object_id.label("object_id"), func.count().label("tags_count")])
        .where(objects_tags.c.tag_id.in_(tags_filter))
        .group_by(objects_tags.c.object_id)
    ).alias("t_f_subquery")
    tags_filter_query = (
        select([tags_filter_subquery.c.object_id]).select_from(tags_filter_subquery)
        .where(tags_filter_subquery.c.tags_count == len(tags_filter))
    ).as_scalar()

    # Get object ids
    result = await conn.execute(select([objects.c.object_id])
            .where(func.lower(objects.c.object_name).like(filter_text))
            .where(objects.c.object_type.in_(object_types))
            .where(objects.c.object_id.in_(tags_filter_query) if len(tags_filter) > 0 else 1 == 1)
            .order_by(order_by if order_asc else order_by.desc())
            .limit(items_per_page)
            .offset(first)
            )
    object_ids = []
    for row in await result.fetchall():
        object_ids.append(row["object_id"])
    
    if len(object_ids) == 0:
        raise web.HTTPNotFound(text = error_json("No objects found."), content_type = "application/json")

    # Get object count
    result = await conn.execute(select([func.count()]).select_from(objects)
                                .where(objects.c.object_name.like(filter_text))
                                .where(objects.c.object_type.in_(object_types)))
    total_items = (await result.fetchone())[0]

    # Send response
    response = {
        "page": p["page"],
        "items_per_page": items_per_page,
        "total_items": total_items,
        "order_by": p["order_by"],
        "sort_order": p["sort_order"],
        "filter_text": p["filter_text"],
        "object_types": object_types,
        "object_ids": object_ids
    }
    return web.json_response(response)


async def search(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = objects_search_schema)

    # Set query params
    conn = request["conn"]
    objects = request.app["tables"]["objects"]
    query_text = "%" + data["query"]["query_text"] + "%"
    maximum_values = data["query"].get("maximum_values", 10)
    existing_ids = data["query"].get("existing_ids", [])

    # Get object ids
    result = await conn.execute(select([objects.c.object_id])
                                .where(and_(
                                    func.lower(objects.c.object_name).like(func.lower(query_text)),
                                    objects.c.object_id.notin_(existing_ids)
                                ))
                                .limit(maximum_values)
    )
    object_ids = []
    for row in await result.fetchall():
        object_ids.append(row["object_id"])
    
    if len(object_ids) == 0:
        raise web.HTTPNotFound(text = error_json("No objects found."), content_type = "application/json")

    return web.json_response({"object_ids": object_ids})


async def update_tags(request):
    # Perform basic data validation
    data = await request.json()
    validate(instance = data, schema = objects_update_tags_schema)

    # Update objects_tags and send response
    conn = request["conn"]
    response_data = {}
    # Update tags
    response_data["tag_updates"] = await update_objects_tags(request, data, check_ids = True)
    
    # Set objects' modified_at time
    response_data["modified_at"] = str(await set_modified_at(request, data["object_ids"]))

    return web.json_response(response_data)


def get_func_name(route, object_type):
    return globals()[f"{route}_{object_type}"]


def get_object_data_update_schema(object_type):
    return globals()[f"{object_type}_object_data"]


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("/add", add, name = "add"),
                    web.put("/update", update, name = "update"),
                    web.delete("/delete", delete, name = "delete"),
                    web.post("/view", view, name = "view"),
                    web.post("/get_page_object_ids", get_page_object_ids, name = "get_page_object_ids"),
                    web.post("/search", search, name = "search"),
                    web.put("/update_tags", update_tags, name = "update_tags"),
                ])
    return app