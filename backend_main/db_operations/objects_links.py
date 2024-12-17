"""
    Link-specific database operations.
"""
from aiohttp import web
from sqlalchemy import select

from backend_main.db_operations.auth import get_objects_data_auth_filter_clause

from backend_main.util.json import link_data_row_proxy_to_dict, error_json
from backend_main.util.searchables import add_searchable_updates_for_objects
from backend_main.validation.db_operations.object_data import validate_link


async def add_links(request, obj_ids_and_data):
    new_links = [{
        "object_id": o["object_id"], 
        "link": o["object_data"]["link"],
        "show_description_as_link": o["object_data"]["show_description_as_link"]
    } for o in obj_ids_and_data]
    for nl in new_links:
        validate_link(nl["link"])
    
    links = request.config_dict["tables"]["links"]
    await request["conn"].execute(
        links.insert()
        .values(new_links)
    )

    # Add objects as pending for `searchables` update
    add_searchable_updates_for_objects(request, [o["object_id"] for o in obj_ids_and_data])


async def update_links(request, obj_ids_and_data):
    for o in obj_ids_and_data:
        new_link = {
            "object_id": o["object_id"], 
            "link": o["object_data"]["link"],
            "show_description_as_link": o["object_data"]["show_description_as_link"]
        }
        validate_link(new_link["link"])
        
        links = request.config_dict["tables"]["links"]
        result = await request["conn"].execute(
            links.update()
            .where(links.c.object_id == o["object_id"])
            .values(new_link)
            .returning(links.c.object_id)
        )

        # Raise an error if object data does not exist
        if not await result.fetchone():
            msg = "Attempted to update a non-link object as a link."
            request["log_event"]("WARNING", "db_operation", msg, details=f"object_id = {o['object_id']}")
            raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")
        
    # Add objects as pending for `searchables` update
    add_searchable_updates_for_objects(request, [o["object_id"] for o in obj_ids_and_data])


async def view_links(request, object_ids):
    links = request.config_dict["tables"]["links"]

    # Objects filter for non 'admin` user level (also filters objects with provided `object_ids`)
    objects_data_auth_filter_clause = get_objects_data_auth_filter_clause(request, links.c.object_id, object_ids)

    records = await request["conn"].execute(
        select(links.c.object_id, links.c.link, links.c.show_description_as_link)
        .where(objects_data_auth_filter_clause)
    )
    result = []
    for row in await records.fetchall():
        result.append(link_data_row_proxy_to_dict(row))
    return result       
