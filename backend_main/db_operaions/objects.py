"""
    Common operations for updating objects table.
"""
from datetime import datetime


async def set_modified_at(request, conn, object_ids, modified_at = None):
    # Check parameter values
    object_ids = object_ids or None
    if type(object_ids) != list:
        raise TypeError("object_ids is not a list or an empty list")

    modified_at = modified_at or datetime.utcnow()
    if type(modified_at) != datetime:
        raise TypeError("modified_at is not a datetime object")

    # Update modified_at
    objects = request.app["tables"]["objects"]
    await conn.execute(objects.update()
                    .where(objects.c.object_id.in_(object_ids))
                    .values(modified_at = modified_at)
                    )
    
    return modified_at
