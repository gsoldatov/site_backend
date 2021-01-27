"""
    Markdown-specific database operations.
"""
from sqlalchemy import select

from backend_main.util.json import markdown_data_row_proxy_to_dict


async def add_markdown(request, obj_id_and_data):
    object_data = {"object_id": obj_id_and_data["object_id"], "raw_text": obj_id_and_data["object_data"]["raw_text"]}

    markdown = request.app["tables"]["markdown"]
    await request["conn"].execute(
        markdown.insert()
        .values(object_data)
    ) 


async def update_markdown(request, obj_id_and_data):
    object_data = {"object_id": obj_id_and_data["object_id"], "raw_text": obj_id_and_data["object_data"]["raw_text"]}

    markdown = request.app["tables"]["markdown"]
    await request["conn"].execute(
        markdown.update()
        .where(markdown.c.object_id == obj_id_and_data["object_id"])
        .values(object_data)
    )


async def view_markdown(request, object_ids):
    markdown = request.app["tables"]["markdown"]
    records = await request["conn"].execute(
        select([markdown.c.object_id, markdown.c.raw_text])
        .where(markdown.c.object_id.in_(object_ids))
    )
    result = []
    for row in await records.fetchall():
        result.append(markdown_data_row_proxy_to_dict(row))
    return result


async def delete_markdown(request, object_ids):
    markdown = request.app["tables"]["markdown"]
    await request["conn"].execute(
        markdown.delete()
        .where(markdown.c.object_id.in_(object_ids))
    )
