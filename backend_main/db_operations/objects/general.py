from sqlalchemy import select, func
from sqlalchemy.sql import and_, true
from sqlalchemy.sql.functions import coalesce

from backend_main.auth.query_clauses import get_objects_auth_filter_clause

from backend_main.util.exceptions import ObjectsNotFound, ObjectIsNotComposite

from sqlalchemy.sql.expression import Select
from backend_main.types.app import app_tables_key, app_config_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.objects.general import ObjectsPaginationInfo, \
    ObjectsPaginationInfoWithResult, ObjectsSearchQuery, CompositeHierarchy


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


async def search_objects(request: Request, query: ObjectsSearchQuery) -> list[int]:
    """ Returns a list of object IDs matching the provided `query`. """
    objects = request.config_dict[app_tables_key].objects
    query_text = "%" + query.query_text + "%"

    # Objects filter for non 'admin` user level
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids_subquery=(
        select(objects.c.object_id)
        .where(and_(
            func.lower(objects.c.object_name).like(func.lower(query_text)),
            objects.c.object_id.notin_(query.existing_ids)
        ))
    ))

    # Get object ids
    result = await request[request_connection_key].execute(
        select(objects.c.object_id)
        .where(and_(
            objects_auth_filter_clause,
            func.lower(objects.c.object_name).like(func.lower(query_text)),
            objects.c.object_id.notin_(query.existing_ids)
        ))
        .limit(query.maximum_values)
    )
    object_ids = [r[0] for r in await result.fetchall()]    
    if len(object_ids) == 0: raise ObjectsNotFound
    return object_ids


async def view_composite_hierarchy(request: Request, object_id: int) -> CompositeHierarchy:
    """
    Returns all object IDs in the composite hierarchy, which starts from `object_id`.
    Maximum depth of hierarchy, which is checked, is limited by `composite_hierarchy_max_depth` configuration setting.
    """
    objects = request.config_dict[app_tables_key].objects
    composite = request.config_dict[app_tables_key].composite

    # Check if object is composite and can be viewed by request sender
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=[object_id])
    result = await request[request_connection_key].execute(
        select(objects.c.object_type)
        .where(and_(
            objects_auth_filter_clause,
            objects.c.object_id == object_id
        ))
    )
    row = await result.fetchone()
    if not row: raise ObjectsNotFound
    if row[0] != "composite": raise ObjectIsNotComposite        

    # Build a hierarchy
    parent_object_ids = set([object_id])
    all_composite = set([object_id])
    all_non_composite: set[int] = set()
    current_depth = 1
    max_depth = request.config_dict[app_config_key].app.composite_hierarchy_max_depth

    while len(parent_object_ids) > 0 and current_depth < max_depth:
        # Query all subobjects of current parents
        result = await request[request_connection_key].execute(
            select(composite.c.subobject_id, objects.c.object_type)
            .select_from(composite.join(objects, composite.c.subobject_id == objects.c.object_id))
            .where(composite.c.object_id.in_(parent_object_ids))    # Do not apply auth filter here (it will be applied when objects' attributes & data are fetched)
        )

        # Get sets with new composite & non-composite object ids
        new_composite: set[int] = set()
        new_non_composite: set[int] = set()
        for row in await result.fetchall():
            s = new_composite if row["object_type"] == "composite" else new_non_composite
            s.add(row["subobject_id"])
        
        # Combine new & total sets of object IDs and exit the loop if there is no new composite objects, which were not previously fetched in the loop
        all_non_composite.update(new_non_composite)

        non_fetched_composite = new_composite.difference(all_composite)
        all_composite.update(non_fetched_composite)
        parent_object_ids = non_fetched_composite
        current_depth += 1
    
    return CompositeHierarchy(composite=list(all_composite), non_composite=list(all_non_composite))


async def delete_objects(request: Request, object_ids: list[int]) -> None:
    """
    Deletes objects with provided `object_ids`.

    Raises an exception, if at least one object does not exist
    """
    # Handle empty `object_ids`
    if len(object_ids) == 0: return

    objects = request.config_dict[app_tables_key].objects
    object_ids_set = set((i for i in object_ids))
    
    # Run delete query & return result
    result = await request[request_connection_key].execute(
        objects.delete()
        .where(objects.c.object_id.in_(object_ids))
        .returning(objects.c.object_id)
    )
    deleted_object_ids = set((r[0] for r in await result.fetchall()))
    non_existing_ids = object_ids_set.difference(deleted_object_ids)
    if len(non_existing_ids) > 0: raise ObjectsNotFound(f"Objects {non_existing_ids} do not exist.")
