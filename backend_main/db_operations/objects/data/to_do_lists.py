"""
Database operations with to-do list objects.
"""
from sqlalchemy import select

from backend_main.auth.query_clauses import get_objects_data_auth_filter_clause

from collections.abc import Collection
from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.objects.data import ToDoListIDTypeData


async def upsert_to_do_lists(request: Request, data: list[ToDoListIDTypeData]) -> None:
    """ Upserts to-do list objects' data into the database. """
    if len(data) == 0: return

    # Delete old data in main table
    to_do_lists = request.config_dict[app_tables_key].to_do_lists
    object_ids = set(o.object_id for o in data)
    await request[request_connection_key].execute(
        to_do_lists.delete()
        .where(to_do_lists.c.object_id.in_(object_ids))
    )

    # Insert new data in main table
    values = [{"object_id": o.object_id, **o.object_data.model_dump(exclude={"items"})} for o in data]

    await request[request_connection_key].execute(
        to_do_lists.insert()
        .values(values)
    )

    # Delete old data in items' table
    to_do_list_items = request.config_dict[app_tables_key].to_do_list_items
    await request[request_connection_key].execute(
        to_do_list_items.delete()
        .where(to_do_list_items.c.object_id.in_(object_ids))
    )

    # Insert new data in items' table
    items_values = [{"object_id": o.object_id, **i.model_dump()} for o in data for i in o.object_data.items]

    await request[request_connection_key].execute(
        to_do_list_items.insert()
        .values(items_values)
    )


async def view_to_do_lists(request: Request, object_ids: Collection[int]) -> list[ToDoListIDTypeData]:
    # Handle empty `object_ids`
    if len(object_ids) == 0: return []

    to_do_lists = request.config_dict[app_tables_key].to_do_lists
    to_do_list_items = request.config_dict[app_tables_key].to_do_list_items

    # Objects filter for non 'admin` user level (also filters objects with provided `object_ids`)
    objects_data_auth_filter_clause = get_objects_data_auth_filter_clause(request, to_do_lists.c.object_id, object_ids)
    objects_data_auth_filter_clause_items = get_objects_data_auth_filter_clause(request, to_do_list_items.c.object_id, object_ids)

    # Query to-do list general object data
    rows = await request[request_connection_key].execute(
        select(
            to_do_lists.c.object_id,
            to_do_lists.c.sort_type
        ).where(objects_data_auth_filter_clause)
    )

    object_data_map = {}
    for r in await rows.fetchall():
        object_data = {**r, "items": []}
        object_id = object_data.pop("object_id")
        object_data_map[object_id] = object_data

    # Query to-do list items
    rows = await request[request_connection_key].execute(
        select(
            to_do_list_items.c.object_id,
            to_do_list_items.c.item_number,
            to_do_list_items.c.item_state,
            to_do_list_items.c.item_text,
            to_do_list_items.c.commentary,
            to_do_list_items.c.indent,
            to_do_list_items.c.is_expanded
        ).where(objects_data_auth_filter_clause_items)
        .order_by(to_do_list_items.c.object_id, to_do_list_items.c.item_number)
    )
    
    for r in await rows.fetchall():
        item = {**r}
        object_id = item.pop("object_id")
        object_data_map[object_id]["items"].append(item)
    
    # Return correctly formatted object data
    return [ToDoListIDTypeData.model_validate({
        "object_id": object_id,
        "object_type": "to_do_list",
        "object_data": object_data
    }) for object_id, object_data in object_data_map.items()]
