from collections.abc import Sequence
from psycopg2._psycopg import connection

from backend_main.db_operations.searchables.tag_processing import process_tag_batch
from backend_main.db_operations.searchables.tag_processing_async import process_tag_batch_coro
from backend_main.db_operations.searchables.object_processing import process_object_batch
from backend_main.db_operations.searchables.object_processing_async import process_object_batch_coro

from backend_main.types.app import app_engine_key
from backend_main.types.request import Request, request_searchables_connection_key


def update_searchables(
        conn: connection,
        tag_ids: Sequence[int] | None = None,
        object_ids: Sequence[int] | None = None
    ) -> None:
    """
    Performs synchronous batched update of searchable data for the provided tag and object IDs.
    Arguments:
    - psycopg2 connection `conn`;
    - lists of tag and object IDs `tag_ids` and `object_ids`.
    """
    tag_ids = tag_ids or tuple()
    object_ids = object_ids or tuple()

    # Process updated tags in batches
    for i in range(0, len(tag_ids), 1000):
        process_tag_batch(conn, tag_ids[i:i+1000])

    # Process updated objects in batches
    for i in range(0, len(object_ids), 1000):
        process_object_batch(conn, object_ids[i:i+1000])


async def update_searchables_coro(
        request: Request,
        tag_ids: Sequence[int],
        object_ids: Sequence[int]
    ) -> None:
    """
    Runs asynchronously batched updates of searchable data for provided `tag_ids` and `object_ids`
    """
    async with request.config_dict[app_engine_key].acquire() as conn:
        request[request_searchables_connection_key] = conn

        # Process updated tags in batches
        for i in range(0, len(tag_ids), 1000):
            await process_tag_batch_coro(request, tag_ids[i:i+1000])

        # Process updated objects in batches
        for i in range(0, len(object_ids), 1000):
            await process_object_batch_coro(request, object_ids[i:i+1000])
