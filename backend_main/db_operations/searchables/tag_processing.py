from datetime import datetime

from backend_main.db_operations.searchables.data_classes import SearchableItem, SearchableCollection


def process_tag_ids(conn, tag_ids):
    """
    Gets tag data, processes it and updates `searchables` table for the provided `tag_ids`.
    """
    if len(tag_ids) == 0: return

    modified_at = datetime.utcnow()

    # psycopg2 connection context processes all executed statements in a transaction
    with conn:
        cursor = conn.cursor()
        
        # Process tag name
        searchables = _process_tags(cursor, tag_ids)

        if len(searchables) > 0:
            # Delete existing searchable data
            cursor.execute("DELETE FROM searchables WHERE tag_id IN %(tag_ids)s", {"tag_ids": tag_ids})

            # Insert new searchable data
            query = "INSERT INTO searchables (tag_id, modified_at, text_a, text_b, text_c) VALUES " + \
                ", ".join("(%s, %s, %s, %s, %s)" for i in range(len(searchables)))
            params = []
            for item in searchables.items.values():
                params.extend((item.item_id, modified_at, item.text_a, item.text_b, item.text_c))
            
            cursor.execute(query, params)
        
        cursor.close()


def _process_tags(cursor, tag_ids):
    """
    Returns searchable text from `tags` table for the provided `tag_ids`.
    """
    query = "SELECT tag_id, tag_name, tag_description FROM tags WHERE tag_id IN %(tag_ids)s"
    cursor.execute(query, {"tag_ids": tag_ids})
    result = SearchableCollection()

    for r in cursor: 
        tag_id, tag_name, tag_description = r

        item = SearchableItem(tag_id, text_a=tag_name)

        # TODO add tag_description to item
        # ```
        # markdown_important, markdown_regular = process_markdown(tag_description)
        # item += process_markdown(tag_id, text_b = markdown_important)
        # item += process_markdown(tag_id, text_b = markdown_regular)
        # ```
        # where `process_markdown` returns a tuple with important (headers, ???) and regular text (other + link URLs)
        # both important and regular texts are then added with the weight B for the description
        
        result.add_item(item)
    
    return result
