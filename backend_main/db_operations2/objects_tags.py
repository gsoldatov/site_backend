"""
    Data base operations with objects_tags table.
"""
from aiohttp import web
from psycopg2.errors import ForeignKeyViolation
from sqlalchemy import select, func, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import and_

from backend_main.auth.route_checks.objects import authorize_objects_modification, authorize_tagged_objects_modification
from backend_main.auth.query_clauses import get_objects_auth_filter_clause, get_tags_auth_filter_clause
from backend_main.middlewares.connection import start_transaction

from backend_main.util.exceptions import ObjectsTagsNotFound
from backend_main.util.json import error_json
from backend_main.util.searchables import add_searchable_updates_for_tags
from backend_main.validation.util import RequestValidationException

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_time_key, request_log_event_key, request_user_info_key, request_connection_key
from backend_main.types.domains.objects_tags import ObjectsTagsMap


async def add_objects_tags(request: Request, object_ids: list[int], tag_ids: list[int]) -> None:
    """
    Inserts all pairs of `object_ids` and `tag_ids` into the `objects_tags` table.
    Ignores already existing pairs.
    """
    if len(object_ids) == 0 or len(tag_ids) == 0: return

    objects_tags = request.config_dict[app_tables_key].objects_tags
    pairs = [{"object_id": object_id, "tag_id": tag_id} for object_id in object_ids for tag_id in tag_ids]

    try:
        await request[request_connection_key].execute(
            insert(objects_tags)
            .values(pairs)
            .on_conflict_do_nothing(index_elements=["object_id", "tag_id"])
        )
    except ForeignKeyViolation as e:
        raise ObjectsTagsNotFound(e)


async def view_objects_tags(request: Request, object_ids: list[int]) -> ObjectsTagsMap:
    """
    Returns a mapping between `object_ids` and lists of their current tags' IDs.
    """
    objects = request.config_dict[app_tables_key].objects
    objects_tags = request.config_dict[app_tables_key].objects_tags
    
    # Objects filter for non 'admin` user level
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


async def delete_objects_tags(request: Request, object_ids: list[int], tag_ids: list[int]) -> None:
    """ Removes all tags with `tag_ids` from `object_ids`. """
    objects_tags = request.config_dict[app_tables_key].objects_tags

    await request[request_connection_key].execute(
        objects_tags.delete()
        .where(and_(
                objects_tags.c.object_id.in_(object_ids), 
                objects_tags.c.tag_id.in_(tag_ids)
        ))
        .returning(objects_tags.c.tag_id)
    )
