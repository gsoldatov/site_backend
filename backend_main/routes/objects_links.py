"""
    Link-specific database operations.
"""
from backend_main.routes.util import validate_url

async def add_link(request, conn, obj_data):
    new_link = {"object_id": obj_data["object_id"], "link": obj_data["object_data"]["link"]}
    validate_url(new_link["link"])

    urls = request.app["tables"]["urls"]
    await conn.execute(urls.insert().\
            values(new_link)
    )


async def update_link(request, conn, obj_data):
    new_link = {"object_id": obj_data["object_id"], "link": obj_data["object_data"]["link"]}
    validate_url(new_link["link"])

    urls = request.app["tables"]["urls"]
    await conn.execute(urls.update().\
        values(new_link)
    )        


async def delete_link(request, conn, object_ids):
    urls = request.app["tables"]["urls"]
    await conn.execute(urls.delete().\
        where(urls.c.object_id.in_(object_ids))
    )
