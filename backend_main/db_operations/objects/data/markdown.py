"""
Database operations with markdown objects.
"""
from sqlalchemy import select

from backend_main.auth.query_clauses import get_objects_data_auth_filter_clause

from collections.abc import Collection
from backend_main.types.app import app_tables_key
from backend_main.types.request import Request, request_connection_key
from backend_main.types.domains.objects.data import MarkdownIDTypeData


async def upsert_markdown(request: Request, data: list[MarkdownIDTypeData]) -> None:
    """ Upserts markdown objects' data into the database. """
    if len(data) == 0: return

    # Delete old data
    markdown = request.config_dict[app_tables_key].markdown
    object_ids = set(o.object_id for o in data)
    await request[request_connection_key].execute(
        markdown.delete()
        .where(markdown.c.object_id.in_(object_ids))
    )

    # Insert new data
    values = [{"object_id": o.object_id, **o.object_data.model_dump()} for o in data]

    await request[request_connection_key].execute(
        markdown.insert()
        .values(values)
    )


async def view_markdown(request: Request, object_ids: Collection[int]) -> list[MarkdownIDTypeData]:
    # Handle empty `object_ids`
    if len(object_ids) == 0: return []
    
    markdown = request.config_dict[app_tables_key].markdown

    # Objects filter for non 'admin` user level (also filters objects with provided `object_ids`)
    objects_data_auth_filter_clause = get_objects_data_auth_filter_clause(request, markdown.c.object_id, object_ids)

    rows = await request[request_connection_key].execute(
        select(markdown.c.object_id, markdown.c.raw_text)
        .where(objects_data_auth_filter_clause)
    )    
    result = []
    for row in await rows.fetchall():
        object_data = {**row}
        result.append(
            MarkdownIDTypeData.model_validate({
                "object_id": object_data.pop("object_id"),
                "object_type": "markdown",
                "object_data": object_data
        }))
    return result
