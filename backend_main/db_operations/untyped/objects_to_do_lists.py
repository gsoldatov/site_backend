"""
    Database operations with to-do lists object data.
"""
from aiohttp import web

from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_objects
from backend_main.types._jsonschema.db_operations.object_data import validate_to_do_list

from backend_main.types.app import app_tables_key
from backend_main.types.request import request_log_event_key, request_connection_key


async def add_to_do_lists(request, obj_ids_and_data):
    to_do_lists = request.config_dict[app_tables_key].to_do_lists
    to_do_list_items = request.config_dict[app_tables_key].to_do_list_items

    new_to_do_lists = []
    new_to_do_list_items = []

    # Validate & prepare data for queries
    for o in obj_ids_and_data:
        object_data = o["object_data"]
        validate_to_do_list(object_data["items"])

        new_to_do_lists.append({"object_id": o["object_id"], "sort_type": object_data["sort_type"]})
        new_to_do_list_items.extend(({
            "object_id": o["object_id"],
            "item_number": item["item_number"],
            "item_state": item["item_state"],
            "item_text": item["item_text"],
            "commentary": item["commentary"],
            "indent": item["indent"],
            "is_expanded": item["is_expanded"]
        } for item in object_data["items"]))

    # Insert to-do list general object data
    await request[request_connection_key].execute(
        to_do_lists.insert()
        .values(new_to_do_lists)
    )

    # Insert to-do list items
    await request[request_connection_key].execute(
        to_do_list_items.insert()
        .values(new_to_do_list_items)
    )

    # Add objects as pending for `searchables` update
    add_searchable_updates_for_objects(request, [o["object_id"] for o in obj_ids_and_data])


async def update_to_do_lists(request, obj_ids_and_data):
    for o in obj_ids_and_data:
        # Validate & prepare data for queries
        object_data = o["object_data"]
        validate_to_do_list(object_data["items"])

        to_do_lists = request.config_dict[app_tables_key].to_do_lists
        to_do_list_items = request.config_dict[app_tables_key].to_do_list_items

        new_to_do_list = {"object_id": o["object_id"], "sort_type": object_data["sort_type"]}
        new_to_do_list_items = [{
            "object_id": o["object_id"],
            "item_number": item["item_number"],
            "item_state": item["item_state"],
            "item_text": item["item_text"],
            "commentary": item["commentary"],
            "indent": item["indent"],
            "is_expanded": item["is_expanded"]
        } for item in object_data["items"]]

        # Update to-do list general object data
        result = await request[request_connection_key].execute(
            to_do_lists.update()
            .where(to_do_lists.c.object_id == o["object_id"])
            .values(new_to_do_list)
            .returning(to_do_lists.c.object_id)
        )

        # Raise an error if object data does not exist
        if not await result.fetchone():
            msg = "Attempted to update a non to-do list object as a to-do list."
            request[request_log_event_key]("WARNING", "db_operation", msg, details={"object_id": o["object_id"]})
            raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")

        # Update to-do list items
        await request[request_connection_key].execute(
            to_do_list_items.delete()
            .where(to_do_list_items.c.object_id == o["object_id"])
        )

        await request[request_connection_key].execute(
            to_do_list_items.insert()
            .values(new_to_do_list_items)
        )

    # Add objects as pending for `searchables` update
    add_searchable_updates_for_objects(request, [o["object_id"] for o in obj_ids_and_data])
