from psycopg2.extensions import AsIs


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
