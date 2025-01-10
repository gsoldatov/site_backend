from aiohttp import web
from jsonschema import validate

from backend_main.middlewares.connection import start_transaction
from backend_main.db_operations.tags import get_page_tag_ids_data
from backend_main.domains.tags import add_tag, update_tag, view_tags, delete_tags, search_tags
from backend_main.domains.objects_tags import add_objects_tags, delete_objects_tags
from backend_main.middlewares.connection import start_transaction

from backend_main.validation.schemas.tags import tags_get_page_tag_ids_schema

from backend_main.types.request import Request, request_time_key, request_log_event_key
from backend_main.types.domains.tags import AddedTag, Tag
from backend_main.types.routes.tags import TagsAddRequestBody, TagsAddUpdateResponseBody, \
    TagsUpdateRequestBody, TagsViewRequestBody, TagsViewResponseBody, TagsDeleteRequestBody, TagsDeleteResponseBody, \
    TagsSearchRequestBody, TagsSearchResponseBody


async def add(request: Request) -> TagsAddUpdateResponseBody:
    # Validate request data
    data = TagsAddRequestBody.model_validate(await request.json())

    # Start a transaction
    await start_transaction(request)

    # Add tag
    added_tag = AddedTag.model_validate({**data.tag.model_dump(), **{
        "created_at": request[request_time_key], "modified_at": request[request_time_key]
    }})
    tag = await add_tag(request, added_tag)

    # Add tag's objects
    added_objects_tags = await add_objects_tags(request, data.tag.added_object_ids, [tag.tag_id])

    # Log and return response
    response = TagsAddUpdateResponseBody.model_validate({"tag": {
        **tag.model_dump(),
        "added_object_ids": added_objects_tags.object_ids,
        "removed_object_ids": []
    }})

    request[request_log_event_key]("INFO", "route_handler", f"Finished adding tag.", details=f"tag_id = {tag.tag_id}.")
    return response


async def update(request: Request) -> TagsAddUpdateResponseBody:
    # Validate request data
    data = TagsUpdateRequestBody.model_validate(await request.json())

    # Start a transaction
    await start_transaction(request)

    # Update tag
    tag = Tag.model_validate({**data.tag.model_dump(), **{
        "created_at": request[request_time_key], "modified_at": request[request_time_key]
    }})
    updated_tag = await update_tag(request, tag)

    # Update tag's objects
    added_objects_tags = await add_objects_tags(request, data.tag.added_object_ids, [tag.tag_id])
    removed_objects_tags = await delete_objects_tags(request, data.tag.removed_object_ids, [tag.tag_id])
    
    # Log and return response
    response = TagsAddUpdateResponseBody.model_validate({"tag": {
        **updated_tag.model_dump(),
        "added_object_ids": added_objects_tags.object_ids,
        "removed_object_ids": removed_objects_tags.object_ids
    }})
    request[request_log_event_key]("INFO", "route_handler", f"Finished updating tag.", details=f"tag_id = {tag.tag_id}.")
    return response


async def view(request: Request) -> TagsViewResponseBody:
    # Validate request data
    data = TagsViewRequestBody.model_validate(await request.json())

    # Get tag attributes
    tags = await view_tags(request, data.tag_ids)
    
    # Log and return response
    response = TagsViewResponseBody(tags=tags)
    request[request_log_event_key]("INFO", "route_handler", "Returning tags.", 
                                   details=f"tag_ids = {data.tag_ids}")
    return response


async def delete(request: Request) -> TagsDeleteResponseBody:
    # Validate request data
    data = TagsDeleteRequestBody.model_validate(await request.json())
    
    # Cascade delete tags
    await delete_tags(request, data.tag_ids)
    
    # Log and return response
    response = TagsDeleteResponseBody(tag_ids=data.tag_ids)
    request[request_log_event_key]("INFO", "route_handler", "Deleted tags.", details=f"tag_ids = {data.tag_ids}")
    return response


async def get_page_tag_ids(request):
    # Validate request data
    data = await request.json()
    validate(instance = data, schema = tags_get_page_tag_ids_schema)
    
    result = await get_page_tag_ids_data(request, data["pagination_info"])
    request[request_log_event_key]("INFO", "route_handler", "Returning page tag IDs.")
    return result
        

async def search(request: Request) -> TagsSearchResponseBody:
    # Validate request data
    data = TagsSearchRequestBody.model_validate(await request.json())

    # Search tags
    tag_ids = await search_tags(request, data.query)
    request[request_log_event_key]("INFO", "route_handler", "Returning tag IDs which match search query.")
    return TagsSearchResponseBody(tag_ids=tag_ids)


def get_subapp():
    app = web.Application()
    app.add_routes([
                    web.post("/add", add, name = "add"),
                    web.put("/update", update, name = "update"),
                    web.post("/view", view, name = "view"),
                    web.delete("/delete", delete, name = "delete"),
                    web.post("/get_page_tag_ids", get_page_tag_ids, name = "get_page_tag_ids"),
                    web.post("/search", search, name = "search")
                ])
    return app
