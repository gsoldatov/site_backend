"""
    Database operations with to-do lists object data.
"""
from sqlalchemy import select

from backend_main.util.json import row_proxy_to_dict
from backend_main.util.validation import validate_to_do_list


async def add_to_do_list(request, obj_id_and_data):
    # Validate & prepare data for queries
    object_data = obj_id_and_data["object_data"]
    validate_to_do_list(object_data["items"])

    to_do_lists = request.app["tables"]["to_do_lists"]
    to_do_list_items = request.app["tables"]["to_do_list_items"]

    new_to_do_list = {"object_id": obj_id_and_data["object_id"], "sort_type": object_data["sort_type"]}
    new_to_do_list_items = [{
        "object_id": obj_id_and_data["object_id"],
        "item_number": item["item_number"],
        "item_state": item["item_state"],
        "item_text": item["item_text"],
        "commentary": item["commentary"],
        "indent": item["indent"],
        "is_expanded": item["is_expanded"]
    } for item in object_data["items"]]

    # Insert to-do list general object data
    await request["conn"].execute(
        to_do_lists.insert()
        .values(new_to_do_list)
    )

    # Insert to-do list items
    await request["conn"].execute(
        to_do_list_items.insert()
        .values(new_to_do_list_items)
    )


async def update_to_do_list(request, obj_id_and_data):
    # Validate & prepare data for queries
    object_data = obj_id_and_data["object_data"]
    validate_to_do_list(object_data["items"])

    to_do_lists = request.app["tables"]["to_do_lists"]
    to_do_list_items = request.app["tables"]["to_do_list_items"]

    new_to_do_list = {"object_id": obj_id_and_data["object_id"], "sort_type": object_data["sort_type"]}
    new_to_do_list_items = [{
        "object_id": obj_id_and_data["object_id"],
        "item_number": item["item_number"],
        "item_state": item["item_state"],
        "item_text": item["item_text"],
        "commentary": item["commentary"],
        "indent": item["indent"],
        "is_expanded": item["is_expanded"]
    } for item in object_data["items"]]

    # Update to-do list general object data
    await request["conn"].execute(
        to_do_lists.update()
        .where(to_do_lists.c.object_id == obj_id_and_data["object_id"])
        .values(new_to_do_list)
    )

    # Update to-do list items
    await request["conn"].execute(
        to_do_list_items.delete()
        .where(to_do_list_items.c.object_id == obj_id_and_data["object_id"])
    )

    await request["conn"].execute(
        to_do_list_items.insert()
        .values(new_to_do_list_items)
    )


async def view_to_do_list(request, object_ids):
    to_do_lists = request.app["tables"]["to_do_lists"]
    to_do_list_items = request.app["tables"]["to_do_list_items"]

    # Query to-do list general object data
    records = await request["conn"].execute(
        select([to_do_lists.c.object_id, to_do_lists.c.sort_type])
        .where(to_do_lists.c.object_id.in_(object_ids))
    )

    data = {}
    for row in await records.fetchall():
        data[row["object_id"]] = { "sort_type": row["sort_type"], "items": [] }

    # Query to-do list items
    items = await request["conn"].execute(
        select([to_do_list_items.c.object_id, to_do_list_items.c.item_number, to_do_list_items.c.item_state, to_do_list_items.c.item_text,
                to_do_list_items.c.commentary, to_do_list_items.c.indent, to_do_list_items.c.is_expanded])
        .where(to_do_list_items.c.object_id.in_(object_ids))
        .order_by(to_do_list_items.c.object_id, to_do_list_items.c.item_number)
    )
    
    for item in await items.fetchall():
        item_dict = row_proxy_to_dict(item)
        object_id = item_dict.pop("object_id")
        # object_id = item["object_id"]
        data[object_id]["items"].append(item_dict)
    
    # Return correctly formatted object data
    return [{ "object_id": k, "object_data": data[k] } for k in data]
