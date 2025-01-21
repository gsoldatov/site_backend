from typing import get_args

from backend_main.db_operations.objects.attributes import view_objects_types as _view_objects_types
from backend_main.db_operations.objects.data.links import view_links as _view_links
from backend_main.db_operations.objects.data.markdown import view_markdown as _view_markdown
from backend_main.db_operations.objects.data.to_do_lists import view_to_do_lists as _view_to_do_lists
from backend_main.db_operations.objects.data.composite import view_composite as _view_composite

from backend_main.types.request import Request
from backend_main.types.domains.objects.attributes import ObjectType
from backend_main.types.domains.objects.data import ObjectIDTypeData


async def view_objects_data(request: Request, object_ids: list[int]) -> list[ObjectIDTypeData]:
    if len(object_ids) == 0: return []

    # Get object types of `object_ids`
    # (for multiple objects set all object types)
    object_types = await _view_objects_types(request, object_ids) \
        if len(object_ids) < 4 else get_args(ObjectType)
    
    # Query object data of each required type
    result: list[ObjectIDTypeData] = []
    
    if "link" in object_types:
        result += await _view_links(request, object_ids)
    if "markdown" in object_types:
        result += await _view_markdown(request, object_ids)
    if "to_do_list" in object_types:
        result += await _view_to_do_lists(request, object_ids)
    if "composite" in object_types:
        result += await _view_composite(request, object_ids)
    
    return result
