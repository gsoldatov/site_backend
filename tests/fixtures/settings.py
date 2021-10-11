from psycopg2.extensions import AsIs


def set_setting(db_cursor, setting_name, setting_value = None, is_public = None):
    if setting_value is None and is_public is None:
        raise TypeError("At least one of `setting_value` and `is_public` must be passed")
    params = [AsIs("settings")]
    if setting_value is not None: params.append(setting_value)
    if is_public is not None: params.append(is_public)
    params.append(setting_name)

    query = "UPDATE %s SET "
    if setting_value is not None: query += "setting_value = %s" + (", " if is_public is not None else "")
    if is_public is not None: query += "is_public = %s"
    query += " WHERE setting_name = %s"
    
    db_cursor.execute(query, params)
