"""
    Link-specific database operations.
"""
from backend_main.routes.util import validate_url

async def add(request, conn, obj_data):
    new_link = {"object_id": obj_data["object_id"], "link": obj_data["object_data"]["link"]}
    validate_url(new_link["link"])

    url_links = request.app["tables"]["url_links"]
    result = await conn.execute(url_links.insert().\
        # returning(url_links.c.object_id, url_links.c.link).\
        values(new_link)
        )
    # record = await result.fetchone()

