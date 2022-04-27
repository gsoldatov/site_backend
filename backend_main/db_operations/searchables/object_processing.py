from datetime import datetime

from backend_main.db_operations.searchables.data_classes import SearchableItem, SearchableCollection
from backend_main.db_operations.searchables.markdown import markdown_to_searchable_item


def process_object_ids(conn, object_ids):
    """
    Gets objects' attributes & data, processes them and updates `searchables` table for the provided `object_ids`.
    """
    if len(object_ids) == 0: return

    modified_at = datetime.utcnow()

    # psycopg2 connection context processes all executed statements in a transaction
    with conn:
        cursor = conn.cursor()
        
        # Process objects
        searchables = _process_objects(cursor, object_ids)

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


def _process_objects(cursor, object_ids):
    """
    Returns searchable text from `objects` table for the provided `object_ids`.
    """
    # Process attributes and get `object_type` for each `object_id`
    query = "SELECT object_id, object_name, object_description, object_type FROM objects WHERE object_id IN %(object_ids)s"
    cursor.execute(query, {"object_ids": object_ids})
    result = SearchableCollection()

    types = {"link": [], "markdown": [], "to_do_list": []}

    for r in cursor: 
        object_id, object_name, object_description, object_type = r
        
        item = SearchableItem(object_id, text_a=object_name)
        item += markdown_to_searchable_item(object_description, item_id=object_id)
        result.add_item(item)


        if object_type in types: types[object_type].append(object_id)
    
    # Process `link` object data
    if len(types["link"]) > 0:
        query = "SELECT object_id, link FROM links WHERE object_id IN %(object_ids)s"
        cursor.execute(query, {"object_ids": tuple(types["link"])})

        for r in cursor:
            object_id, link = r
            item = SearchableItem(object_id, text_b=link)
            result.add_item(item)
    
    # Process `markdown` object data
    if len(types["markdown"]) > 0:
        query = "SELECT object_id, raw_text FROM markdown WHERE object_id IN %(object_ids)s"
        cursor.execute(query, {"object_ids": tuple(types["markdown"])})

        for r in cursor:
            object_id, raw_text = r
            item = markdown_to_searchable_item(raw_text, item_id=object_id)
            result.add_item(item)
    
    # Process `to_do_list` object data
    if len(types["to_do_list"]) > 0:
        query = "SELECT object_id, item_text, commentary FROM to_do_list_items WHERE object_id IN %(object_ids)s"
        cursor.execute(query, {"object_ids": tuple(types["to_do_list"])})
        tdl_searchables = SearchableCollection()

        for r in cursor:
            object_id, item_text, commentary = r
            item = SearchableItem(object_id, text_b=item_text, text_c=commentary)
            tdl_searchables.add_item(item)
        
        result += tdl_searchables
    
    return result
