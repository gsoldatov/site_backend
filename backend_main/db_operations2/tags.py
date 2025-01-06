from sqlalchemy import select, func

from backend_main.util.searchables import add_searchable_updates_for_tags

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key, request_time_key, request_log_event_key
from backend_main.types.domains.tags import TagNameToIDMap


async def add_tags_by_name(request: Request, tag_names: list[str]) -> TagNameToIDMap:
    """
    Adds tags for each name from `tag_names`, which does not exist in the database.
    Returns a mapping between tag names and added or existing tag IDs.
    """
    if len(tag_names) == 0: return {}

    tags = request.config_dict[app_tables_key].tags

    # Get IDs for existing tag names
    lowered_names_to_names = {n.lower(): n for n in tag_names}  # tag lowercase name to name map
    lowered_names = {n.lower() for n in tag_names}

    result = await request[request_connection_key].execute(
        select(tags.c.tag_id, func.lower(tags.c.tag_name).label("lowered_tag_name"))
        .where(func.lower(tags.c.tag_name).in_(lowered_names))
    )

    existing_lowered_names_to_ids: dict[str, int] = {
        row["lowered_tag_name"]: row["tag_id"] for row in result.fetchall()
    }
    existing_names_to_ids = {lowered_names_to_names[k]: v for k, v in existing_lowered_names_to_ids.items()}

    # Exit if all tags already exist
    new_tag_names = {n for n in tag_names if n not in existing_names_to_ids}
    if len(new_tag_names) == 0:
        return TagNameToIDMap(map=existing_names_to_ids)

    # Insert unmapped tag names
    request_time = request[request_time_key]
    new_tag_ids = []

    result = await request[request_connection_key].execute(
        tags.insert()
        .returning(tags.c.tag_id, tags.c.tag_name)
        .values([{
            "created_at": request_time,
            "modified_at": request_time,
            "tag_name": name,
            "tag_description": "",
            "is_published": True
        } for name in new_tag_names])
    )

    new_names_to_ids: dict[str, int] = {row["tag_name"]: row["tag_id"] for row in result.fetchall()}
    
    # Add new tags as pending for `searchables` update
    request[request_log_event_key](
        "INFO", "db_operation","Added new tags by name.", details=f"tag_ids = {new_tag_ids}"
    )
    add_searchable_updates_for_tags(request, new_tag_ids)

    # Returns tag name to ID mapping
    return TagNameToIDMap(map={**existing_names_to_ids, **new_names_to_ids})
