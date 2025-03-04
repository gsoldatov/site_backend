from psycopg2.extensions import AsIs


def insert_objects(objects, db_cursor, generate_ids = False):
    """
    Inserts a list of objects into objects table.
    If `generate_ids` is True, values for object IDs will be generated by the database.
    """
    # Query
    field_names = ["object_id", "object_type", "created_at", "modified_at", "object_name", "object_description", "is_published",
        "display_in_feed", "feed_timestamp", "show_description", "owner_id"]
    if generate_ids: field_names = field_names[1:]
    fields_tuple = "(" + ", ".join(field_names) + ")"
    values = "(" + ", ".join(["%s"] * len(field_names)) + ")"
    query = f"INSERT INTO %s {fields_tuple} VALUES " + ", ".join((values for _ in range(len(objects))))

    # Params
    params = [AsIs("objects")]
    for o in objects:
        for field in field_names:
            params.append(o[field])
    db_cursor.execute(query, params)


def insert_links(links, db_cursor):
    """
    Inserts link objects' data into the database.
    `links` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {"link": ...}}
    """
    field_names = ("object_id", "link", "show_description_as_link")
    query = "INSERT INTO %s" + str(field_names).replace("'", '"') + " VALUES " \
        + ", ".join(("(%s, %s, %s)" for _ in range(len(links))))
    params = [AsIs("links")]
    for l in links:
        params.append(l["object_id"])
        params.append(l["object_data"]["link"])
        params.append(l["object_data"]["show_description_as_link"])
    db_cursor.execute(query, params)


def insert_markdown(markdown, db_cursor):
    """
    Inserts markdown objects' data into the database.
    `markdown` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {"raw_text": ...}}
    """
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(markdown))))
    table = "markdown"
    params = [AsIs(table)]
    for m in markdown:
        params.append(m["object_id"])
        params.append(m["object_data"]["raw_text"])
    db_cursor.execute(query, params)


def insert_to_do_lists(lists, db_cursor):
    """
    Inserts to-do list objects' data into the database.
    `lists` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {...}}
    """
    # to_do_lists
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s)" for _ in range(len(lists))))
    table = "to_do_lists"
    params = [AsIs(table)]
    for l in lists:
        params.extend([l["object_id"], l["object_data"]["sort_type"]])
    db_cursor.execute(query, params)

    # to_do_list_items
    num_of_lines = sum((len(t["object_data"]["items"]) for t in lists))
    query = "INSERT INTO %s VALUES " + ", ".join(("(%s, %s, %s, %s, %s, %s, %s)" for _ in range(num_of_lines)))
    table = "to_do_list_items"
    params = [AsIs(table)]
    for l in lists:
        for i in l["object_data"]["items"]:
            params.append(l["object_id"])
            params.extend(i.values())
    db_cursor.execute(query, params)


def insert_composite(composite, db_cursor):
    """
    Inserts composite objects' data into the database (both composite properties and subobjects).
    `composite` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {...}}
    """
    field_names = ("object_id", "subobject_id", "column", "row", "selected_tab", "is_expanded", "show_description_composite", "show_description_as_link_composite")
    num_of_lines = sum((len(c["object_data"]["subobjects"]) for c in composite))
    query = "INSERT INTO %s" + str(field_names).replace("'", '"') + " VALUES " \
        + ", ".join(("(%s, %s, %s, %s, %s, %s, %s, %s)" for _ in range(num_of_lines)))
    params = [AsIs("composite")]
    for c in composite:
        for so in c["object_data"]["subobjects"]:
            params.append(c["object_id"])
            for field in field_names:
                if field == "object_id":
                    pass
                else:
                    params.append(so[field])
    db_cursor.execute(query, params)

    # Insert composite_properties
    insert_composite_properties(composite, db_cursor)


def insert_composite_properties(composite, db_cursor):
    """
    Inserts composite properties into the database.
    `composite` is an array with elements as dict objects with the folowing structure:
    {"object_id": ..., "object_data: {...}}
    """
    field_names = ("object_id", "display_mode", "numerate_chapters")
    query = "INSERT INTO %s" + str(field_names).replace("'", '"') + " VALUES " \
        + ", ".join(("(%s, %s, %s)" for _ in range(len(composite))))
    params = [AsIs("composite_properties")]
    for c in composite:
        params.append(c["object_id"])
        params.append(c["object_data"]["display_mode"])
        params.append(c["object_data"]["numerate_chapters"])
    db_cursor.execute(query, params)


def delete_objects(object_ids, db_cursor):
    """
    Deletes objects with provided IDs (this should also result in a cascade delete of related data from other tables).
    """
    table = "objects"
    query = "DELETE FROM %s WHERE object_id IN (" + ", ".join(("%s" for _ in range(len(object_ids)))) + ")"
    params = [AsIs(table)]
    params.extend(object_ids)
    db_cursor.execute(query, params)


object_data_insert_functions = {
    "link": insert_links,
    "markdown": insert_markdown,
    "to_do_list": insert_to_do_lists,
    "composite": insert_composite
}
