from backend_main.db_operations.searchables.tag_processing import process_tag_batch
from backend_main.db_operations.searchables.tag_processing_async import process_tag_batch_coro
from backend_main.db_operations.searchables.object_processing import process_object_batch
from backend_main.db_operations.searchables.object_processing_async import process_object_batch_coro


def update_searchables(conn, tag_ids = None, object_ids = None):
    """
    Performs batched update of searchable data for the provided tag and object IDs.
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


async def update_searchables_coro(request, tag_ids, object_ids):
    """
    Runs batched updates of searchable data for provided `tag_ids` and `object_ids`
    """
    async with request.config_dict["engine"].acquire() as conn:
        request["conn_searchables"] = conn

        # Process updated tags in batches
        for i in range(0, len(tag_ids), 1000):
            await process_tag_batch_coro(request, tag_ids[i:i+1000])

        # Process updated objects in batches
        for i in range(0, len(object_ids), 1000):
            await process_object_batch_coro(request, object_ids[i:i+1000])
