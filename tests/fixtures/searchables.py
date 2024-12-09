from datetime import datetime, timezone

from psycopg2.extensions import AsIs


def get_test_searchable(object_id = None, tag_id = None, modified_at = None, text_a = None, text_b = None, text_c = None, pop_keys = []):
    """
    Returns a new dictionary for `searchables` table with attributes specified in `pop_keys` popped from it.
    Either `object_id` or `tag_id` must be provided. Other values can be provided to override default values.
    """
    if tag_id is None and object_id is None: raise TypeError("Either tag_id or object_id must be specified")

    modified_at = modified_at if modified_at is not None else datetime.now(tz=timezone.utc)
    searchable = {"object_id": object_id, "tag_id": tag_id, "modified_at": modified_at, "text_a": text_a, "text_b": text_b, "text_c": text_c}

    for k in pop_keys: searchable.pop(k, None)

    return searchable


def insert_searchables(searchables, db_cursor):
    """
    Inserts a list of `searchables` into searchables table.
    """
    # query
    field_order = ["object_id", "tag_id", "modified_at", "text_a", "text_b", "text_c"]
    fields_tuple = "(" + ", ".join(field_order) + ")"
    query = f"INSERT INTO %s {fields_tuple} VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s)" for _ in range(len(searchables))))
    
    # params
    table = "searchables"
    params = [AsIs(table)]
    for u in searchables:
        for f in field_order:
            params.append(u[f])

    db_cursor.execute(query, params)
