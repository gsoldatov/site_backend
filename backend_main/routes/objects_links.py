"""
    Link-specific database operations.
"""
from backend_main.routes.util import validate_link

async def add_link(request, conn, obj_data):
    new_link = {"object_id": obj_data["object_id"], "link": obj_data["object_data"]["link"]}
    validate_link(new_link["link"])

    links = request.app["tables"]["links"]
    await conn.execute(links.insert().\
            values(new_link)
    )


async def update_link(request, conn, obj_data):
    new_link = {"object_id": obj_data["object_id"], "link": obj_data["object_data"]["link"]}
    validate_link(new_link["link"])

    links = request.app["tables"]["links"]
    await conn.execute(links.update().\
        values(new_link)
    )        


async def delete_link(request, conn, object_ids):
    links = request.app["tables"]["links"]
    await conn.execute(links.delete().\
        where(links.c.object_id.in_(object_ids))
    )
