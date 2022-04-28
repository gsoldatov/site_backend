from backend_main.db_operations.searchables.tag_processing import process_tag_ids
from backend_main.db_operations.searchables.object_processing import process_object_ids


def update_searchables(conn, tag_ids = tuple(), object_ids = tuple()):
    """
    Performs batched update of searchable data for the provided tag and object IDs.
    Arguments:
    - psycopg2 connection `conn`;
    - lists of tag and object IDs `tag_ids` and `object_ids`.
    """
    # Process updated tags in batches
    for i in range(0, len(tag_ids), 1000):
        process_tag_ids(conn, tag_ids[i:i+1000])

    # Process updated objects in batches
    for i in range(0, len(object_ids), 1000):
        process_object_ids(conn, object_ids[i:i+1000])
