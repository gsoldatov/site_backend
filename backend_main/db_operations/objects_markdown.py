"""
    Markdown-specific database operations.
"""
from aiohttp import web
from sqlalchemy import select

from backend_main.db_operations.auth import get_objects_data_auth_filter_clause

from backend_main.util.json import markdown_data_row_proxy_to_dict, error_json
from backend_main.util.searchables import add_searchable_updates_for_objects

from backend_main.types.app import app_tables_key
from backend_main.types.request import request_log_event_key, request_connection_key


async def add_markdown(request, obj_ids_and_data):
    object_data = [{"object_id": o["object_id"], "raw_text": o["object_data"]["raw_text"]} for o in obj_ids_and_data]

    markdown = request.config_dict[app_tables_key].markdown
    await request[request_connection_key].execute(
        markdown.insert()
        .values(object_data)
    )
    
    # Add objects as pending for `searchables` update
    add_searchable_updates_for_objects(request, [o["object_id"] for o in obj_ids_and_data])


async def update_markdown(request, obj_ids_and_data):
    markdown = request.config_dict[app_tables_key].markdown

    for o in obj_ids_and_data:
        object_data = {"object_id": o["object_id"], "raw_text": o["object_data"]["raw_text"]}

        result = await request[request_connection_key].execute(
            markdown.update()
            .where(markdown.c.object_id == o["object_id"])
            .values(object_data)
            .returning(markdown.c.object_id)
        )

        # Raise an error if object data does not exist
        if not await result.fetchone():
            msg = "Attempted to update a non-markdown object as a markdown."
            request[request_log_event_key]("WARNING", "db_operation", msg, details=f"object_id = {o['object_id']}")
            raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")
        
    # Add objects as pending for `searchables` update
    add_searchable_updates_for_objects(request, [o["object_id"] for o in obj_ids_and_data])


async def view_markdown(request, object_ids):
    markdown = request.config_dict[app_tables_key].markdown

    # Objects filter for non 'admin` user level (also filters objects with provided `object_ids`)
    objects_data_auth_filter_clause = get_objects_data_auth_filter_clause(request, markdown.c.object_id, object_ids)

    records = await request[request_connection_key].execute(
        select(markdown.c.object_id, markdown.c.raw_text)
        .where(objects_data_auth_filter_clause)
    )
    result = []
    for row in await records.fetchall():
        result.append(markdown_data_row_proxy_to_dict(row))
    return result
