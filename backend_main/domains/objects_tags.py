from backend_main.db_operations2.objects_tags import view_objects_tags as _view_objects_tags, \
    view_tags_objects as _view_tags_objects

from backend_main.types.request import Request
from backend_main.types.domains.objects_tags import ObjectsTagsMap


async def view_objects_tags(request: Request, object_ids: list[int]) -> ObjectsTagsMap:
    return await _view_objects_tags(request, object_ids)


async def view_tags_objects(request: Request, tag_ids: list[int]) -> ObjectsTagsMap:
    return await _view_tags_objects(request, tag_ids)
