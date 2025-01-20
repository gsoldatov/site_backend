from backend_main.auth.route_checks.objects import authorize_objects_modification

from backend_main.db_operations2.objects.attributes import update_modified_at as _update_modified_at, \
    view_objects_attributes_and_tags as _view_objects_attributes_and_tags

from datetime import datetime
from backend_main.types.request import Request
from backend_main.types.domains.objects.attributes import ObjectAttributesAndTags


async def update_modified_at(request: Request, object_ids: list[int], modified_at: datetime) -> datetime:
    # Authorize update operation
    await authorize_objects_modification(request, object_ids)

    # Update attribute & return
    return await _update_modified_at(request, object_ids, modified_at)


async def view_objects_attributes_and_tags(request: Request, object_ids: list[int]) -> list[ObjectAttributesAndTags]:
    if len(object_ids) == 0: return []
    return await _view_objects_attributes_and_tags(request, object_ids)