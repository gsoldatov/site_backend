"""
    Link-specific database operations.
"""
from sqlalchemy import select

from backend_main.util.json import link_data_row_proxy_to_dict
from backend_main.util.validation import validate_link


async def add_link(request, obj_data):
    new_link = {"object_id": obj_data["object_id"], "link": obj_data["object_data"]["link"]}
    validate_link(new_link["link"])

    links = request.app["tables"]["links"]
    await request["conn"].execute(
        links.insert()
        .values(new_link)
    )


async def view_link(request, object_ids):
    links = request.app["tables"]["links"]
    records = await request["conn"].execute(
        select([links.c.object_id, links.c.link])
        .where(links.c.object_id.in_(object_ids))
    )
    result = []
    for row in await records.fetchall():
        result.append(link_data_row_proxy_to_dict(row))
    return result


async def update_link(request, obj_data):
    new_link = {"object_id": obj_data["object_id"], "link": obj_data["object_data"]["link"]}
    validate_link(new_link["link"])
    
    links = request.app["tables"]["links"]
    await request["conn"].execute(
        links.update()
        .where(links.c.object_id == obj_data["object_id"])
        .values(new_link)
    )        


async def delete_link(request, object_ids):
    links = request.app["tables"]["links"]
    await request["conn"].execute(
        links.delete()
        .where(links.c.object_id.in_(object_ids))
    )
