from psycopg2.extensions import AsIs


def set_setting(setting_name, setting_value, db_cursor, config):
    table = config["db"]["db_schema"] + ".settings"
    params = [AsIs(table)]
    params.extend((setting_value, setting_name))
    db_cursor.execute("UPDATE %s SET setting_value = %s WHERE setting_name = %s", params)
