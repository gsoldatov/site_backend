"""
Database initialization + migration module.
"""
import os, sys
import subprocess

import psycopg2

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(sys.path[0])))

from backend_main.config import get_config
    

def connect(host, port, database, user, password):
    connection = psycopg2.connect(host = host, port = port, database = database, \
                            user = user, password = password)
    connection.set_session(autocommit=True)
    
    return connection.cursor()


def disconnect(cursor):
    if cursor:
        if cursor.connection:
            cursor.close()
            cursor.connection.close()


def create_user(cursor, user, password):
    cursor.execute(f"""DO $$
                        BEGIN
                            CREATE ROLE {user} PASSWORD '{password}' LOGIN;
                            EXCEPTION WHEN DUPLICATE_OBJECT THEN
                            RAISE NOTICE 'Not creating {user} role, because it already exists.';
                        END
                    $$;""")
    while cursor.connection.notices:
        print(cursor.connection.notices.pop())
    print("Finished creating the user.")


def create_db(cursor, db_name, db_owner):
    cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
    cursor.execute(f"CREATE DATABASE {db_name} ENCODING 'UTF-8' OWNER {db_owner} TEMPLATE template0;")
    print("Finished creating the database.")


def create_schema(host, port, database, user, password, schema):
    cursor = None
    try:
        cursor = connect(host, port, database, user, password)
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION {user};")
        print("Finished creating the schema.")
    finally:
        disconnect(cursor)
    

def create_flyway_conf(db_config, folder):    
    conf_file = folder + "/flyway.conf"

    host = db_config["db_host"]
    port = db_config["db_port"]
    database = db_config["db_database"]
    user = db_config["db_username"]
    password = db_config["db_password"]
    schema = db_config["db_schema"]

    if not os.path.exists(folder):
        os.mkdir(folder)
    
    if os.path.exists(conf_file):
        os.remove(conf_file)
        
    with open(conf_file, "w") as write_stream:
        write_stream.write("\n".join([
           f"flyway.url=jdbc:postgresql://{host}:{port}/{database}",
           f"flyway.user={user}",
           f"flyway.password={password}",
           f"flyway.schemas={schema}",
           f"flyway.locations=filesystem:./"
        ]))
    
    print("Finished creating flyway.conf file.")


def migrate_db(folder):
    p = subprocess.Popen(["flyway", "migrate"], shell = True, cwd = folder)
    p.wait()


def init_db():
    cursor = None
    
    try:
        db_config  = get_config()["db"]
        cursor = connect(host = db_config["db_host"], port = db_config["db_port"], database = db_config["db_init_database"],
                            user = db_config["db_init_username"], password = db_config["db_init_password"])
        if db_config["create_user_required"]:
            create_user(cursor, db_config["db_username"], db_config["db_password"])
        create_db(cursor, db_config["db_database"], db_config["db_username"])
        create_schema(host = db_config["db_host"], port = db_config["db_port"], database = db_config["db_database"],
                        user = db_config["db_username"], password = db_config["db_password"], 
                        schema = db_config["db_schema"])
    finally:
        disconnect(cursor)
    
    migrations_folder = os.path.dirname(os.path.abspath(__file__)) + "/migrations"
    create_flyway_conf(db_config, migrations_folder)
    migrate_db(migrations_folder)


if __name__ == "__main__":
    init_db()