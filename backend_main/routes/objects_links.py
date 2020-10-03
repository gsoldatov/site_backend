"""
    Link-specific database operations.
"""
from backend_main.routes.util import validate_url

async def add(request, conn, obj_data):
    new_link = {"object_id": obj_data["object_id"], "link": obj_data["object_data"]["link"]}
    validate_url(new_link["link"])

    urls = request.app["tables"]["urls"]
    result = await conn.execute(urls.insert().\
        # returning(urls.c.object_id, urls.c.link).\
        values(new_link)
        )
    # record = await result.fetchone()

