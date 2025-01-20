from sqlalchemy import select
from sqlalchemy.sql import and_
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.dialects.postgresql import array_agg

from backend_main.auth.query_clauses import get_objects_auth_filter_clause

from datetime import datetime
from typing import cast
from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.objects.attributes import ObjectAttributesAndTags, ObjectType


async def update_modified_at(request: Request, object_ids: list[int], modified_at: datetime) -> datetime:
    """
    Updates `modified_at` attribute of the objects with provided `object_ids` to the provided value.
    Returns the updated `modified_at` value.
    """
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
    objects = request.config_dict[app_tables_key].objects
    objects_tags = request.config_dict[app_tables_key].objects_tags

    # Objects filter for non 'admin` user level
    objects_auth_filter_clause = get_objects_auth_filter_clause(request, object_ids=object_ids)

    tags_subquery = select(
        objects_tags.c.object_id,
        array_agg(objects_tags.c.tag_id).label("current_tag_ids")
    ) \
    .where(and_(
        objects_auth_filter_clause,
        objects_tags.c.object_id.in_(object_ids)
    )) \
    .group_by(objects_tags.c.object_id) \
    .subquery()

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
