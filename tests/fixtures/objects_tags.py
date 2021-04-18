from psycopg2.extensions import AsIs


def insert_objects_tags(object_ids, tag_ids, db_cursor, config):
    """
    Inserts a all possible pairs of object and tag ids into <db_schema>.objects_tags table.
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(tag_ids) * len(object_ids)) ))
    table = config["db"]["db_schema"] + ".objects_tags"
    params = [AsIs(table)]
    for t in tag_ids:
        for o in object_ids:
            params.extend((t, o))
    db_cursor.execute(query, params)