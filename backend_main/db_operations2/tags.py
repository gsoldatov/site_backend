from sqlalchemy import select, func
from sqlalchemy.sql import and_

from backend_main.auth.query_clauses import get_tags_auth_filter_clause

from backend_main.util.exceptions import TagsNotFound
from backend_main.util.searchables import add_searchable_updates_for_tags

from sqlalchemy.sql.expression import Select
from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_log_event_key, request_connection_key, request_time_key
from backend_main.types.domains.tags import Tag, AddedTag, TagNameToIDMap, \
    TagsPaginationInfo, TagsPaginationInfoWithResult, TagsSearchQuery


async def add_tag(request: Request, added_tag: AddedTag) -> Tag:
    """
    Insert a new row into "tags" table with provided `new_tag` attributes.
    """
    tags = request.config_dict[app_tables_key].tags
    values = added_tag.model_dump()

    result = await request[request_connection_key].execute(
        tags.insert()
        .returning(
            tags.c.tag_id,
            tags.c.created_at,
            tags.c.modified_at,
            tags.c.tag_name,
            tags.c.tag_description,
            tags.c.is_published
        ).values(values)
    )

    row = await result.fetchone()
    return Tag.model_validate({**row})


async def add_tags_by_name(request: Request, tag_names: list[str]) -> TagNameToIDMap:
    """
    Adds tags for each name from `tag_names`, which does not exist in the database.
    Returns a mapping between tag names and added or existing tag IDs.
    """
    if len(tag_names) == 0: return TagNameToIDMap(map={})

    tags = request.config_dict[app_tables_key].tags

    # Get IDs for existing tag names
    lowered_names_to_names = {n.lower(): n for n in tag_names}  # tag lowercase name to name map
    lowered_names = {n.lower() for n in tag_names}

    result = await request[request_connection_key].execute(
        select(tags.c.tag_id, func.lower(tags.c.tag_name).label("lowered_tag_name"))
        .where(func.lower(tags.c.tag_name).in_(lowered_names))
    )

    existing_lowered_names_to_ids: dict[str, int] = {
        row["lowered_tag_name"]: row["tag_id"] for row in await result.fetchall()
    }
    existing_names_to_ids = {lowered_names_to_names[k]: v for k, v in existing_lowered_names_to_ids.items()}

    # Exit if all tags already exist
    new_tag_names = {n for n in tag_names if n not in existing_names_to_ids}
    if len(new_tag_names) == 0:
        return TagNameToIDMap(map=existing_names_to_ids)

    # Insert unmapped tag names
    request_time = request[request_time_key]

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

    new_names_to_ids: dict[str, int] = {row["tag_name"]: row["tag_id"] for row in await result.fetchall()}
    new_tag_ids: list[int] = [v for v in new_names_to_ids.values()]
    
    # Add new tags as pending for `searchables` update
    request[request_log_event_key](
        "INFO", "db_operation","Added new tags by name.", details=f"tag_ids = {new_tag_ids}"
    )
    add_searchable_updates_for_tags(request, new_tag_ids)

    # Returns tag name to ID mapping
    return TagNameToIDMap(map={**existing_names_to_ids, **new_names_to_ids})


async def update_tag(request: Request, tag: Tag) -> Tag:
    """
    Updates the tag attributes with provided tag_attributes.
    """
    tags = request.config_dict[app_tables_key].tags
    values = tag.model_dump()

    result = await request[request_connection_key].execute(
        tags.update()
        .where(tags.c.tag_id == tag.tag_id)
        .values(values)
        .returning(
            tags.c.tag_id,
            tags.c.created_at,
            tags.c.modified_at,
            tags.c.tag_name,
            tags.c.tag_description,
            tags.c.is_published
        )
    )
    
    row = await result.fetchone()
    if not row: raise TagsNotFound()
    return Tag.model_validate({**row})


async def view_tags(request: Request, tag_ids: list[int]) -> list[Tag]:
    """
    Returns a list tag attributes for the provided `tag_ids`.
    """
    tags = request.config_dict[app_tables_key].tags

    # Tags auth filter for non-admin user levels
    tags_auth_filter_clause = get_tags_auth_filter_clause(request)

    result = await request[request_connection_key].execute(
        select(tags)
        .where(and_(
            tags_auth_filter_clause,
            tags.c.tag_id.in_(tag_ids))
    ))

    viewed_tags = [Tag.model_validate({**r}) for r in await result.fetchall()]
    if len(viewed_tags) == 0: raise TagsNotFound()
    return viewed_tags


async def delete_tags(request: Request, tag_ids: list[int]) -> None:
    """
    Deletes tags with provided `tag_ids`.
    """
    tags = request.config_dict[app_tables_key].tags
    result = await request[request_connection_key].execute(
        tags.delete()
        .where(tags.c.tag_id.in_(tag_ids))
        .returning(tags.c.tag_id)
    )

    if not await result.fetchone(): raise TagsNotFound()


async def view_page_tag_ids(
    request: Request, 
    pagination_info: TagsPaginationInfo
) -> TagsPaginationInfoWithResult:
    """
    Returns IDs of tags which correspond to the provided pagination_info
    and the total number of matching tags.
    """
    # Set query params
    tags = request.config_dict[app_tables_key].tags
    order_by = tags.c.modified_at if pagination_info.order_by == "modified_at" else tags.c.tag_name
    order_asc = pagination_info.sort_order == "asc"
    items_per_page = pagination_info.items_per_page
    first = (pagination_info.page - 1) * items_per_page
    filter_text = f"%{pagination_info.filter_text.lower()}%"

    # Tags auth filter for non-admin user levels
    tags_auth_filter_clause = get_tags_auth_filter_clause(request)

    # return where clause statements for a select statement `s`.
    def with_where_clause(s: Select):
        return (
            s.where(and_(
                tags_auth_filter_clause,
                func.lower(tags.c.tag_name).like(filter_text)
            ))
        )

    # Get tag ids
    result = await request[request_connection_key].execute(
        with_where_clause(
            select(tags.c.tag_id)
        )
        .order_by(order_by if order_asc else order_by.desc())
        .limit(items_per_page)
        .offset(first)
    )
    tag_ids = [int(r[0]) for r in await result.fetchall()]
    if len(tag_ids) == 0: raise TagsNotFound()

    # Get tag count
    result = await request[request_connection_key].execute(
        with_where_clause(
            select(func.count())
            .select_from(tags)
        )
    )
    total_items = (await result.fetchone())[0]

    return TagsPaginationInfoWithResult.model_validate({
        **pagination_info.model_dump(),
        "tag_ids": tag_ids,
        "total_items": total_items
    })


async def search_tags(request: Request, query: TagsSearchQuery) -> list[int]:
    """
    Returns a list of tag IDs matching the provided query.
    """
    # Set query params
    tags = request.config_dict[app_tables_key].tags
    query_text = "%" + query.query_text + "%"

    # Tags auth filter for non-admin user levels
    tags_auth_filter_clause = get_tags_auth_filter_clause(request)

    # Get tag ids
    result = await request[request_connection_key].execute(
        select(tags.c.tag_id)
        .where(and_(
            tags_auth_filter_clause,
            func.lower(tags.c.tag_name).like(func.lower(query_text)),
            tags.c.tag_id.notin_(query.existing_ids)
        ))
        .limit(query.maximum_values)
    )
    tag_ids = [int(r[0]) for r in await result.fetchall()]
    
    if len(tag_ids) == 0: raise TagsNotFound()
    return tag_ids
