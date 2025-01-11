from sqlalchemy import select, func
from sqlalchemy.sql import and_, true
from sqlalchemy.sql.functions import coalesce

from backend_main.auth.query_clauses import get_objects_auth_filter_clause

from backend_main.util.exceptions import ObjectsNotFound

from sqlalchemy.sql.expression import Select
from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.objects import \
    ObjectsPaginationInfo, ObjectsPaginationInfoWithResult


async def get_exclusive_subobject_ids(request: Request, object_ids: list[int]) -> list[int]:
    """
    Returns a set of object IDs, which are subobjects only to the objects with specified `object_ids`.
    """
    composite = request.config_dict[app_tables_key].composite

    # Get all subobject IDs of deleted subobjects
    result = await request[request_connection_key].execute(
        select(composite.c.subobject_id)
        .distinct()
        .where(composite.c.object_id.in_(object_ids))
    )
    subobjects_of_deleted_objects = set((int(r[0]) for r in await result.fetchall()))

    # Get subobject IDs which are present in other composite objects
    result = await request[request_connection_key].execute(
        select(composite.c.subobject_id)
        .distinct()
        .where(and_(
            composite.c.subobject_id.in_(subobjects_of_deleted_objects),
            composite.c.object_id.notin_(object_ids)
        ))
    )
    subobjects_present_in_other_objects = set((int(r[0]) for r in await result.fetchall()))
    
    # Return subobject IDs which are present only in deleted composite objects
    return [o for o in subobjects_of_deleted_objects if o not in subobjects_present_in_other_objects]


async def delete_objects(request: Request, object_ids: list[int]) -> None:
    """
    Deletes objects with provided `object_ids`.
    """
    objects = request.config_dict[app_tables_key].objects
    
    # Run delete query & return result
    result = await request[request_connection_key].execute(
        objects.delete()
        .where(objects.c.object_id.in_(object_ids))
        .returning(objects.c.object_id)
    )
    if not await result.fetchone(): raise ObjectsNotFound


async def view_page_object_ids(
        request: Request,
        pagination_info: ObjectsPaginationInfo
    ) -> ObjectsPaginationInfoWithResult:
    """
    Get IDs of objects which correspond to the provided `pagination_info`
    and a total number of matching objects.
    """
    objects = request.config_dict[app_tables_key].objects
    objects_tags = request.config_dict[app_tables_key].objects_tags

    # Basic query parameters and clauses
    order_by = {
        "object_name": objects.c.object_name,
        "modified_at": objects.c.modified_at,
        "feed_timestamp": coalesce(objects.c.feed_timestamp, objects.c.modified_at)
    }[pagination_info.order_by]
    order_asc = pagination_info.sort_order == "asc"
    items_per_page = pagination_info.items_per_page
    first = (pagination_info.page - 1) * items_per_page
    show_only_displayed_in_feed = pagination_info.show_only_displayed_in_feed

    # Optional search condidions
    def with_where_clause(s: Select):
        """ Returns where clause statements for a select statement `s`. """
        # Text filter for object name
        filter_text = pagination_info.filter_text
        if len(filter_text) > 0: filter_text = f"%{filter_text.lower()}%"
        text_filter_clause = func.lower(objects.c.object_name).like(filter_text) if len(filter_text) > 0 else true()

        # Object types filter
        object_types = pagination_info.object_types
        object_types_clause = objects.c.object_type.in_(object_types) if len(object_types) > 0 else true()

        # Tags filter
        tags_filter_clause = true()
        if len(pagination_info.tags_filter) > 0:
            tags_filter = pagination_info.tags_filter

            # Sub-query for filtering objects which match tags filter condition
            tags_filter_subquery = (
                select(objects_tags.c.object_id.label("object_id"), func.count().label("tags_count"))
                .where(objects_tags.c.tag_id.in_(tags_filter))
                .group_by(objects_tags.c.object_id)
            ).alias("t_f_subquery")
            tags_filter_query = (
                select(tags_filter_subquery.c.object_id)
                .select_from(tags_filter_subquery)
                .where(tags_filter_subquery.c.tags_count == len(tags_filter))
            ).scalar_subquery()

            tags_filter_clause = objects.c.object_id.in_(tags_filter_query)
        
        # Display in feed
        display_in_feed_clause =  objects.c.display_in_feed == True if show_only_displayed_in_feed else true()

        # Objects filter for non 'admin` user level
        objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids_subquery=(
            select(objects.c.object_id)
            .where(text_filter_clause)
            .where(object_types_clause)
            .where(tags_filter_clause)
            .where(display_in_feed_clause)
        ))
        
        # Resulting statement
        return (
            s
            .where(objects_auth_filter_clause)
            .where(text_filter_clause)
            .where(object_types_clause)
            .where(tags_filter_clause)
            .where(display_in_feed_clause)
        )

    # Get object ids
    result = await request[request_connection_key].execute(
        with_where_clause(
            select(objects.c.object_id)
        )
        .order_by(order_by if order_asc else order_by.desc())
        .limit(items_per_page)
        .offset(first)
    )
    object_ids = [r[0] for r in await result.fetchall()]
    
    if len(object_ids) == 0: raise ObjectsNotFound

    # Get object count
    result = await request[request_connection_key].execute(
        with_where_clause(
            select(func.count())
            .select_from(objects)
        )
    )
    total_items = (await result.fetchone())[0]

    # Return response
    return ObjectsPaginationInfoWithResult.model_validate({
        **pagination_info.model_dump(),
        "object_ids": object_ids,
        "total_items": total_items
    })
