from backend_main.db_operations.searchables.tag_processing import process_tag_ids


def searchables_update_manager(conn, tag_ids = tuple(), object_ids = tuple()):
    """
    Performs batched update of searchable data for the provided tag and object IDs.
    Arguments:
    - psycopg2 connection `conn`;
    - lists of tag and object IDs `tag_ids` and `object_ids`.
    """
    # Process updated tags in batches
    for i in range(0, len(tag_ids), 1000):
        process_tag_ids(conn, tag_ids[i:i+1000])
