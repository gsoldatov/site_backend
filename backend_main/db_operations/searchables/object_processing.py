from datetime import datetime

from backend_main.db_operations.searchables.data_classes import SearchableItem, SearchableCollection


def process_object_ids(conn, object_ids):
    """
    Gets objects' attributes & data, processes them and updates `searchables` table for the provided `object_ids`.
    """
    if len(object_ids) == 0: return

    modified_at = datetime.utcnow()

    # psycopg2 connection context processes all executed statements in a transaction
    with conn:
        cursor = conn.cursor()
        
        # Process attributes
        searchables = _process_objects_attributes(cursor, object_ids)

        if len(searchables) > 0:
            # Delete existing searchable data
            cursor.execute("DELETE FROM searchables WHERE object_id IN %(object_ids)s", {"object_ids": object_ids})

            # Insert new searchable data
            query = "INSERT INTO searchables (object_id, modified_at, text_a, text_b, text_c) VALUES " + \
                ", ".join("(%s, %s, %s, %s, %s)" for i in range(len(searchables)))
            params = []
            for item in searchables.items.values():
                params.extend((item.item_id, modified_at, item.text_a, item.text_b, item.text_c))
            
            cursor.execute(query, params)
        
        cursor.close()


def _process_objects_attributes(cursor, object_ids):
    """
    Returns searchable text from `objects` table for the provided `object_ids`.
    """
    query = "SELECT object_id, object_name, object_description FROM objects WHERE object_id IN %(object_ids)s"
    cursor.execute(query, {"object_ids": object_ids})
    result = SearchableCollection()

    for r in cursor: 
        object_id, object_name, object_description = r

        item = SearchableItem(object_id, text_a=object_name)

        # TODO add object_description to item
        # ```
        # markdown_important, markdown_regular = process_markdown(object_description)
        # item += process_markdown(object_id, text_b = markdown_important)
        # item += process_markdown(object_id, text_b = markdown_regular)
        # ```
        # where `process_markdown` returns a tuple with important (headers, ???) and regular text (other + link URLs)
        # both important and regular texts are then added with the weight B for the description
        
        result.add_item(item)
    
    return result
