import os

import psycopg2
from psycopg2.extensions import cursor as CursorClass
import alembic.config


class DBExistsException(Exception):
    pass


def connect(host, port, database, user, password):
    connection = psycopg2.connect(host=host, port=port, database=database, \
                            user=user, password=password)
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
    if len(cursor.connection.notices) > 0:
        while cursor.connection.notices:
            print(cursor.connection.notices.pop().rstrip())
    else:
        print("Finished creating the user.")


def create_db(cursor, db_name, db_owner, force):
    # Check if db exists
    cursor.execute(f"SELECT COUNT(*) as count FROM pg_database WHERE datname='{db_name}'")
    db_exists = cursor.fetchone()[0]

    if db_exists:
        # Stop if db exists and --force flag is not provided
        if not force:
            raise DBExistsException(f"Database already exists, exiting without recreating and applying migrations.")
        
        # Close connections and drop existing database if --force flag is provided
        cursor.execute(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{db_name}'
                        AND pid <> pg_backend_pid();
        """)
        cursor.execute(f"DROP DATABASE {db_name};")
        print(f"Deleted existing database '{db_name}'.")
    
    cursor.execute(f"CREATE DATABASE {db_name} ENCODING 'UTF-8' OWNER {db_owner} TEMPLATE template0;")
    print("Finished creating the database.")


def revision(message = ""):
    # Set current working directory
    cwd = os.getcwd()
    alembic_dir = os.path.dirname(__file__)
    os.chdir(alembic_dir)

    # Run revision command
    alembic_args = ["revision", "--autogenerate", f'-m "{message}"']
    alembic.config.main(argv=alembic_args)

    # Restore current working directory
    os.chdir(cwd)
    print("Finished database revision.")


def migrate_as_superuser(db_config):
    """Additional migration commands which require as superuser privilege."""
    cursor = connect(host=db_config["db_host"], port=db_config["db_port"], database=db_config["db_database"],
                                user=db_config["db_init_username"], password=db_config["db_init_password"])
    try:
        # Create extension for password storing
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    finally:
        if type(cursor) == CursorClass:
            disconnect(cursor)


def migrate(config_file = None):
    # Set current working directory
    cwd = os.getcwd()
    alembic_dir = os.path.dirname(__file__)
    os.chdir(alembic_dir)

    # Run revision command
    alembic_args = ["-x", f'app_config_path="{config_file}"'] if config_file else []
    alembic_args.extend(["upgrade", "head"])
    alembic.config.main(argv=alembic_args)

    # Restore current working directory
    os.chdir(cwd)
    print("Finished migrating the database.")
