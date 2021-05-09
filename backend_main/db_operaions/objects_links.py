"""
    Link-specific database operations.
"""
from aiohttp import web
from sqlalchemy import select

from backend_main.util.json import link_data_row_proxy_to_dict, error_json
from backend_main.util.validation import validate_link


async def add_links(request, obj_ids_and_data):
    new_links = [{"object_id": o["object_id"], "link": o["object_data"]["link"]} for o in obj_ids_and_data]
    for nl in new_links:
        validate_link(nl["link"])
    
    links = request.app["tables"]["links"]
    await request["conn"].execute(
        links.insert()
        .values(new_links)
    )


async def update_links(request, obj_ids_and_data):
    for o in obj_ids_and_data:
        new_link = {"object_id": o["object_id"], "link": o["object_data"]["link"]}
        validate_link(new_link["link"])
        
        links = request.app["tables"]["links"]
        result = await request["conn"].execute(
            links.update()
            .where(links.c.object_id == o["object_id"])
            .values(new_link)
            .returning(links.c.object_id)
        )

        # Raise an error if object data does not exist
        if not await result.fetchone():
            raise web.HTTPBadRequest(text=error_json(f"Failed to update data of object with object_id '{o['object_id']}': object_id does not belong to a link object."), content_type="application/json")


async def view_links(request, object_ids):
    links = request.app["tables"]["links"]
    records = await request["conn"].execute(
        select([links.c.object_id, links.c.link])
        .where(links.c.object_id.in_(object_ids))
    )
    result = []
    for row in await records.fetchall():
        result.append(link_data_row_proxy_to_dict(row))
    return result       
