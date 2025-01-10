from sqlalchemy import select
from sqlalchemy.sql import and_

from backend_main.util.exceptions import ObjectsNotFound

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key


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
