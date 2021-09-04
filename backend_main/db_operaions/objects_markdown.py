"""
    Markdown-specific database operations.
"""
from aiohttp import web
from sqlalchemy import select

from backend_main.db_operaions.auth import get_objects_data_auth_filter_clause

from backend_main.util.json import markdown_data_row_proxy_to_dict, error_json


async def add_markdown(request, obj_ids_and_data):
    object_data = [{"object_id": o["object_id"], "raw_text": o["object_data"]["raw_text"]} for o in obj_ids_and_data]

    markdown = request.app["tables"]["markdown"]
    await request["conn"].execute(
        markdown.insert()
        .values(object_data)
    ) 


async def update_markdown(request, obj_ids_and_data):
    markdown = request.app["tables"]["markdown"]

    for o in obj_ids_and_data:
        object_data = {"object_id": o["object_id"], "raw_text": o["object_data"]["raw_text"]}

        result = await request["conn"].execute(
            markdown.update()
            .where(markdown.c.object_id == o["object_id"])
            .values(object_data)
            .returning(markdown.c.object_id)
        )

        # Raise an error if object data does not exist
        if not await result.fetchone():
            raise web.HTTPBadRequest(text=error_json(f"Failed to update data of object with object_id '{o['object_id']}': object_id does not belong to a Markdown object."), content_type="application/json")


async def view_markdown(request, object_ids):
    markdown = request.app["tables"]["markdown"]

    # Objects filter for non 'admin` user level (also filters objects with provided `object_ids`)
    auth_filter_clause = get_objects_data_auth_filter_clause(request, object_ids, markdown.c.object_id)

    records = await request["conn"].execute(
        select([markdown.c.object_id, markdown.c.raw_text])
        .where(auth_filter_clause)
        # .where(markdown.c.object_id.in_(object_ids))
    )
    result = []
    for row in await records.fetchall():
        result.append(markdown_data_row_proxy_to_dict(row))
    return result
