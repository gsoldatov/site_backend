"""
    Data base operations with objects_tags table.
"""
from psycopg2.errors import ForeignKeyViolation
from sqlalchemy import select, column, values, Integer
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import and_

from backend_main.auth.query_clauses import get_objects_auth_filter_clause, get_tags_auth_filter_clause

from backend_main.util.exceptions import ObjectsTagsNotFound

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.objects_tags import ObjectTag, ObjectsTagsMap


async def add_objects_tags(request: Request, added_objects_tags: list[ObjectTag]) -> None:
    """
    Inserts pairs of of object and tag IDs from `added_objects_tags` into the `objects_tags` table.
    Ignores already existing pairs.
    """
    # Handle empty objects tags list
    if len(added_objects_tags) == 0: return

    objects_tags = request.config_dict[app_tables_key].objects_tags
    values = [ot.model_dump() for ot in added_objects_tags]

    try:
        await request[request_connection_key].execute(
            insert(objects_tags)
            .values(values)
            .on_conflict_do_nothing(index_elements=["object_id", "tag_id"])
        )
    except ForeignKeyViolation as e:
        raise ObjectsTagsNotFound(e)


async def view_objects_tags(request: Request, object_ids: list[int]) -> ObjectsTagsMap:
    """
    Returns a mapping between `object_ids` and lists of their current tags' IDs.
    """
    # Handle empty `object_ids`
    if len(object_ids) == 0: return ObjectsTagsMap(map={})

    objects = request.config_dict[app_tables_key].objects
    objects_tags = request.config_dict[app_tables_key].objects_tags
    
    # Objects filter for non 'admin` user level
    # NOTE: this also filters objects with non-published tags
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

    result = await request[request_connection_key].execute(
    select(objects_tags.c.object_id, objects_tags.c.tag_id)

    # join objects table to apply objects auth filter
    .select_from(objects_tags.join(objects, objects_tags.c.object_id == objects.c.object_id))

    .where(and_(
        objects_tags.c.object_id.in_(object_ids),   # select rows for provided `object_ids`
        objects_auth_filter_clause                  # filter with objects auth clause
    )))

    map: dict[int, list[int]] = {object_id: [] for object_id in object_ids}

    for row in await result.fetchall():
        map[row["object_id"]].append(row["tag_id"])
    
    return ObjectsTagsMap(map=map)


async def view_tags_objects(request: Request, tag_ids: list[int]) -> ObjectsTagsMap:
    """
    Returns a mapping between `tag_ids` and lists of their current objects' IDs.
    """
    # Handle empty `tag_ids`
    if len(tag_ids) == 0: return ObjectsTagsMap(map={})

    objects = request.config_dict[app_tables_key].objects
    tags = request.config_dict[app_tables_key].tags
    objects_tags = request.config_dict[app_tables_key].objects_tags
    
    tags_auth_filter_clause = get_tags_auth_filter_clause(request, is_published=True)
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids_subquery=(
        select(objects_tags.c.object_id)
        .distinct()
        .where(objects_tags.c.tag_id.in_(tag_ids))
    ))

    # Get pairs wihtout filtering objects with non-published tags
    result = await request[request_connection_key].execute(
    select(objects_tags.c.object_id, objects_tags.c.tag_id)
    .select_from(
            objects_tags
            .join(tags, objects_tags.c.tag_id == tags.c.tag_id))   # join tags table to apply tags auth filter
            .join(objects, objects_tags.c.object_id == objects.c.object_id)
    .where(and_(
        objects_tags.c.tag_id.in_(tag_ids),         # select rows for provided `tag_ids`
        tags_auth_filter_clause,                    # filter with tags auth clause
        objects_auth_filter_clause                  # filter with objects auth clause
    )))

    map: dict[int, list[int]] = {tag_id: [] for tag_id in tag_ids}

    for row in await result.fetchall():
        map[row["tag_id"]].append(row["object_id"])
    
    return ObjectsTagsMap(map=map)


async def delete_objects_tags(request: Request, removed_objects_tags: list[ObjectTag]) -> None:
    """ Removes pairs object object and tag IDs passed via `removed_objects_tags` from the `objects_tags` table. """
    # Handle empty objects tags list
    if len(removed_objects_tags) == 0: return

    objects_tags = request.config_dict[app_tables_key].objects_tags

    # Values clause with deleted pairs
    values_clause = values(
        column("object_id", Integer),
        column("tag_id", Integer),
        name="deleted_pairs"
    ).data((
        (ot.object_id, ot.tag_id) for ot in removed_objects_tags
    ))

    # Correlated subquery, which filters `objects_tags` records based on their presence in `values_clause`
    exists = select(1).where(and_(
        objects_tags.c.object_id == values_clause.c.object_id,
        objects_tags.c.tag_id == values_clause.c.tag_id
    )).exists()

    # Delete pairs on `exists` condition
    # NOTE: filtering by object IDs before applying `exists` may improve
    # performance, should it be needed (another option is to loop over object IDs in SQL)
    query = (
        objects_tags.delete()
        .where(exists)
        .returning(objects_tags.c.tag_id)
    )
    await request[request_connection_key].execute(query)
