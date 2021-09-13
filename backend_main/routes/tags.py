from datetime import datetime

from aiohttp import web
from jsonschema import validate

from backend_main.db_operations.tags import add_tag, update_tag, view_tags, delete_tags, get_page_tag_ids_data, search_tags
from backend_main.db_operations.objects_tags import view_objects_tags, update_objects_tags
from backend_main.schemas.tags import tags_add_schema, tags_update_schema, tags_view_delete_schema, \
    tags_get_page_tag_ids_schema, tags_search_schema
from backend_main.util.json import row_proxy_to_dict


async def add(request):
    # Validate request data and add missing values
    data = await request.json()
    validate(instance = data, schema = tags_add_schema)
    
    # Get and set attribute values
    current_time = datetime.utcnow()
    data["tag"]["created_at"] = current_time
    data["tag"]["modified_at"] = current_time
    added_object_ids = data["tag"].pop("added_object_ids", [])

    # Add the tag
    tag = row_proxy_to_dict(await add_tag(request, data["tag"]))

    # Tag objects with the new tag
    tag["object_updates"] = await update_objects_tags(request, {"tag_ids": [tag["tag_id"]], "added_object_ids": added_object_ids})

    return {"tag": tag}


async def update(request):
    # Validate request data and add missing values
    data = await request.json()
    validate(instance = data, schema = tags_update_schema)

    # Get and set attribute values
    data["tag"]["modified_at"] = datetime.utcnow()
    added_object_ids = data["tag"].pop("added_object_ids", [])
    removed_object_ids = data["tag"].pop("removed_object_ids", [])

    # Update the tag
    tag_id = data["tag"]["tag_id"]
    tag = row_proxy_to_dict(await update_tag(request, data["tag"]))

    # Update object's tags
    tag["object_updates"] = await update_objects_tags(request, 
        {"tag_ids": [tag_id], "added_object_ids": added_object_ids, "removed_object_ids": removed_object_ids})

    return {"tag": tag}


async def view(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = tags_view_delete_schema)

    # Get parameters and initialize container for response data
    tag_ids = data["tag_ids"]
    return_current_object_ids = data.get("return_current_object_ids", False)
    tags = {}

    # Query tag IDs
    for row in await view_tags(request, tag_ids):
        tags[row["tag_id"]] = row_proxy_to_dict(row)
        tags[row["tag_id"]]["current_object_ids"] = []

    # Query tagged objects
    if return_current_object_ids:
        for row in await view_objects_tags(request, tag_ids = tag_ids):
            tags[row["tag_id"]]["current_object_ids"].append(row["object_id"])
    
    response = {"tags": [tags[k] for k in tags]}
    return response


async def delete(request):
    # Validate request data and add missing values
    data = await request.json()
    validate(instance = data, schema = tags_view_delete_schema)
    tag_ids = data["tag_ids"]
    
    # Cascade delete tags
    await delete_tags(request, tag_ids)
    
    # Send response
    response = {"tag_ids": tag_ids}
    return response


async def get_page_tag_ids(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = tags_get_page_tag_ids_schema)
    
    return await get_page_tag_ids_data(request, data["pagination_info"])
        

async def search(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = tags_search_schema)

    # Search tags
    tag_ids = await search_tags(request, data["query"])

    return {"tag_ids": tag_ids}


# async def merge(request):
#     pass


# async def link(request):
#     pass


# async def unlink(request):
#     pass


# async def get_linked(request):
#     pass


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("/add", add, name = "add"),
                    web.put("/update", update, name = "update"),
                    web.post("/view", view, name = "view"),
                    web.delete("/delete", delete, name = "delete"),
                    web.post("/get_page_tag_ids", get_page_tag_ids, name = "get_page_tag_ids"),
                    web.post("/search", search, name = "search")#,
                    # web.put("/merge", merge, name = "merge"),
                    # web.post("/link/{type}", link, name = "link"),
                    # web.delete("/unlink/{type}", unlink, name = "unlink"),
                    # web.get("/get_linked/{id}", get_linked, name="get_linked")
                ])
    return app
