"""
    Database operations with to-do lists object data.
"""
from aiohttp import web
from sqlalchemy import select

from backend_main.db_operations.auth import get_objects_data_auth_filter_clause
from backend_main.middlewares.connection import start_transaction

from backend_main.util.json import row_proxy_to_dict, error_json
from backend_main.util.searchables import add_searchable_updates_for_objects
from backend_main.validation.db_operations.object_data import validate_to_do_list


async def add_to_do_lists(request, obj_ids_and_data):
    to_do_lists = request.config_dict["tables"]["to_do_lists"]
    to_do_list_items = request.config_dict["tables"]["to_do_list_items"]

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
    
    # Ensure a transaction is started
    await start_transaction(request)

    # Insert to-do list general object data
    await request["conn"].execute(
        to_do_lists.insert()
        .values(new_to_do_lists)
    )

    # Insert to-do list items
    await request["conn"].execute(
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

        to_do_lists = request.config_dict["tables"]["to_do_lists"]
        to_do_list_items = request.config_dict["tables"]["to_do_list_items"]

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

        # Ensure a transaction is started
        await start_transaction(request)

        # Update to-do list general object data
        result = await request["conn"].execute(
            to_do_lists.update()
            .where(to_do_lists.c.object_id == o["object_id"])
            .values(new_to_do_list)
            .returning(to_do_lists.c.object_id)
        )

        # Raise an error if object data does not exist
        if not await result.fetchone():
            msg = "Attempted to update a non to-do list object as a to-do list."
            request["log_event"]("WARNING", "db_operation", msg, details=f"object_id = {o['object_id']}")
            raise web.HTTPBadRequest(text=error_json(msg), content_type="application/json")

        # Update to-do list items
        await request["conn"].execute(
            to_do_list_items.delete()
            .where(to_do_list_items.c.object_id == o["object_id"])
        )

        await request["conn"].execute(
            to_do_list_items.insert()
            .values(new_to_do_list_items)
        )

    # Add objects as pending for `searchables` update
    add_searchable_updates_for_objects(request, [o["object_id"] for o in obj_ids_and_data])


async def view_to_do_lists(request, object_ids):
    to_do_lists = request.config_dict["tables"]["to_do_lists"]
    to_do_list_items = request.config_dict["tables"]["to_do_list_items"]

    # Objects filter for non 'admin` user level (also filters objects with provided `object_ids`)
    objects_data_auth_filter_clause = get_objects_data_auth_filter_clause(request, to_do_lists.c.object_id, object_ids)
    objects_data_auth_filter_clause_items = get_objects_data_auth_filter_clause(request, to_do_list_items.c.object_id, object_ids)

    # Query to-do list general object data
    records = await request["conn"].execute(
        select(to_do_lists.c.object_id, to_do_lists.c.sort_type)
        .where(objects_data_auth_filter_clause)
    )

    data = {}
    for row in await records.fetchall():
        data[row["object_id"]] = { "sort_type": row["sort_type"], "items": [] }

    # Query to-do list items
    items = await request["conn"].execute(
        select(to_do_list_items.c.object_id, to_do_list_items.c.item_number, to_do_list_items.c.item_state, to_do_list_items.c.item_text,
                to_do_list_items.c.commentary, to_do_list_items.c.indent, to_do_list_items.c.is_expanded)
        .where(objects_data_auth_filter_clause_items)
        .order_by(to_do_list_items.c.object_id, to_do_list_items.c.item_number)
    )
    
    for item in await items.fetchall():
        item_dict = row_proxy_to_dict(item)
        object_id = item_dict.pop("object_id")
        data[object_id]["items"].append(item_dict)
    
    # Return correctly formatted object data
    return [{ "object_id": k, "object_data": data[k] } for k in data]
