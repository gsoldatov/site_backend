"""
Database operations with link objects.
"""
from sqlalchemy import select

from backend_main.auth.query_clauses import get_objects_data_auth_filter_clause

from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.objects import LinkIDTypeData


async def view_links(request: Request, object_ids: list[int]) -> list[LinkIDTypeData]:
    # Handle empty `object_ids`
    if len(object_ids) == 0: return []
    
    links = request.config_dict[app_tables_key].links

    # Objects filter for non 'admin` user level (also filters objects with provided `object_ids`)
    objects_data_auth_filter_clause = get_objects_data_auth_filter_clause(request, links.c.object_id, object_ids)

    rows = await request[request_connection_key].execute(
        select(
            links.c.object_id,
            links.c.link,
            links.c.show_description_as_link
        ).where(objects_data_auth_filter_clause)
    )
    result = []
    for row in await rows.fetchall():
        object_data = {**row}
        result.append(
            LinkIDTypeData.model_validate({
                "object_id": object_data.pop("object_id"),
                "object_type": "link",
                "object_data": object_data
        }))
    return result
