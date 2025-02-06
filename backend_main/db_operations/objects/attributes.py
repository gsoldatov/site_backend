from psycopg2.errors import ForeignKeyViolation
from sqlalchemy import select
from sqlalchemy.sql import and_
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.dialects.postgresql import array_agg

from backend_main.auth.query_clauses import get_objects_auth_filter_clause

from backend_main.util.exceptions import UserNotFound

from collections.abc import Collection
from datetime import datetime
from typing import cast
from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.objects.general import ObjectsIDsMap
from backend_main.types.domains.objects.attributes import UpsertedObjectAttributes, ObjectAttributesAndTags, ObjectType


async def add_objects(request: Request, objects_attributes: list[UpsertedObjectAttributes]) -> ObjectsIDsMap:
    """
    Inserts provided `objects_attributes` into the database as new objects' attributes (with ID auto generation)
    and returns mapping between provided and generated object IDs.
    """
    if len(objects_attributes) == 0: return ObjectsIDsMap(map={})

    # Sort new objects by their IDs to create a correct old to new ID mapping.
    # Identity should generate new IDs for multiple rows in ascending order for the order they were inserted in:
    # https://stackoverflow.com/questions/50809120/postgres-insert-into-with-select-ordering
    sorted_objects_attributes = sorted(objects_attributes, key=lambda o: o.object_id, reverse=True)
    values = [o.model_dump(exclude={"object_id"}) for o in sorted_objects_attributes]

    # Insert new objects
    objects = request.config_dict[app_tables_key].objects

    try:
        result = await request[request_connection_key].execute(
            objects.insert()
            .returning(objects.c.object_id)
            .values(values))
        
        records = await result.fetchall()

        sorted_new_object_ids = sorted([o["object_id"] for o in records])
        object_id_mapping = {sorted_objects_attributes[i].object_id: sorted_new_object_ids[i] for i in range(len(sorted_new_object_ids))}

        return ObjectsIDsMap(map=object_id_mapping)
    except ForeignKeyViolation as e:
        raise UserNotFound(e)


async def update_objects(request: Request, objects_attributes: list[UpsertedObjectAttributes]) -> None:
    """
    Updates provided existing `objects_attributes` in the database.
    
    NOTE: checks for object existince and type change are done in domain function.
    """
    if len(objects_attributes) == 0: return

    objects = request.config_dict[app_tables_key].objects
    
    for oa in objects_attributes:
        values = oa.model_dump(exclude={"created_at"})
    
        await request[request_connection_key].execute(
            objects.update()
            .where(objects.c.object_id == oa.object_id)
            .values(values)
        )


async def update_modified_at(request: Request, object_ids: list[int], modified_at: datetime) -> datetime:
    """
    Updates `modified_at` attribute of the objects with provided `object_ids` to the provided value.
    Returns the updated `modified_at` value.
    """
    if len(object_ids) > 0:
        # Update modified_at
        objects = request.config_dict[app_tables_key].objects
        await request[request_connection_key].execute(objects.update()
            .where(objects.c.object_id.in_(object_ids))
            .values(modified_at=modified_at)
        )
    return modified_at


async def view_objects_attributes_and_tags(request: Request, object_ids: list[int]) -> list[ObjectAttributesAndTags]:
    """
    Returns attributes and tags of object with provided `object_ids`.
    """
    # Handle empty `object_ids`
    if len(object_ids) == 0: return []

    objects = request.config_dict[app_tables_key].objects
    objects_tags = request.config_dict[app_tables_key].objects_tags

    # Objects filter for non 'admin` user level
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

    tags_subquery = select(
        objects_tags.c.object_id,
        array_agg(objects_tags.c.tag_id).label("current_tag_ids")
    ) \
    .where(objects_tags.c.object_id.in_(object_ids)) \
    .group_by(objects_tags.c.object_id) \
    .subquery()
    # .where(and_(
    #     objects_auth_filter_clause,   # don't apply auth clause for objects' tags, because
    #                                   # 1) `objects_auth_filter_clause` won't work 
    #                                   #    (since it references `objects` table instead of `objects_tags`)
    #                                   #    (although `get_objects_data_auth_filter_clause` can be used instead)
    #                                   # 2) auth clause is applied to main table anyway
    #     objects_tags.c.object_id.in_(object_ids)
    # )) \
    # .group_by(objects_tags.c.object_id) \
    # .subquery()

    query = select(
            objects.c.object_id,
            objects.c.object_type,
            objects.c.created_at,
            objects.c.modified_at,
            objects.c.object_name,
            objects.c.object_description,
            objects.c.is_published,
            objects.c.display_in_feed,
            objects.c.feed_timestamp,
            objects.c.show_description,
            objects.c.owner_id,
            coalesce(tags_subquery.c.current_tag_ids, []).label("current_tag_ids")
        ).outerjoin(tags_subquery, objects.c.object_id == tags_subquery.c.object_id) \
        .where(and_(
            objects_auth_filter_clause,
            objects.c.object_id.in_(object_ids)
        ))

    result = await request[request_connection_key].execute(query)
    data = [ObjectAttributesAndTags.model_validate({**r}) for r in await result.fetchall()]
    return data


async def view_objects_types(request: Request, object_ids: list[int]) -> list[ObjectType]:
    """
    Returns a unique list of object types of the object with the provided `object_ids`.
    """
    # Handle empty `object_ids`
    if len(object_ids) == 0: return []
    
    objects = request.config_dict[app_tables_key].objects

    # Objects filter for non 'admin` user level
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

    result = await request[request_connection_key].execute(
        select(objects.c.object_type)
        .distinct()
        .where(and_(
            objects_auth_filter_clause,
            objects.c.object_id.in_(object_ids)
        ))
    )

    return [cast(ObjectType, r[0]) for r in await result.fetchall()]


async def view_existing_object_ids(
        request: Request,
        object_ids: Collection[int],
        object_types: Collection[ObjectType]
    ) -> set[int]:
    """
    Returns a set of `object_ids`, which existing in `objects` table
    and have provided `object_type`.
    """
    # Handle empty `object_ids`
    if len(object_ids) == 0: return set()

    # Objects filter for non 'admin` user level
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

    objects = request.config_dict[app_tables_key].objects
    result = await request[request_connection_key].execute(
        select(objects.c.object_id)
        .where(and_(
            objects_auth_filter_clause,
            objects.c.object_id.in_(object_ids),
            objects.c.object_type.in_(object_types)
        ))
    )
    return set((cast(int, r[0]) for r in await result.fetchall()))
