import os

import psycopg2
from psycopg2.extensions import cursor as CursorClass
import alembic.config


class InitDBException(Exception):
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


def drop_user_and_db(cursor, db_config, force):
    """
    Removes user and database with `db_username` and `db_database` names specified in the config respectively, if `force` flag is true.
    Checks all existing databases, reassigns all owned objects to default user and removes all privileges granted to default user.
    After that, deletes the user and the database.
    """
    # Validate `db_database` and `db_username` values
    print("Removing existing user and database...")
    print("Validating db_config.")
    db_init_username, db_init_database = db_config["db_init_username"], db_config["db_init_database"]
    db_username, db_database = db_config["db_username"], db_config["db_database"]
    
    if db_init_database == db_database: raise InitDBException("db_init_database and db_database cannot be equal.")    
    if db_database == "template0": raise InitDBException("db_database cannot be equal to 'template0'.")

    # Get user and database
    cursor.execute(f"SELECT usename FROM pg_user WHERE usename = '{db_username}'")
    user_exists = cursor.fetchone() is not None
    cursor.execute(f"SELECT datname FROM pg_catalog.pg_database WHERE datname = '{db_database}'")
    database_exists = cursor.fetchone() is not None

    # If none exists, return
    print(f"db_username exists: {user_exists}, db_database exists: {database_exists}.")
    if not (user_exists or database_exists):
        print("Neither db_username, nor db_database exist, existing removal function.")
        return
    
    # If at least one exists, and force flag is not provided, raise InitDBException
    if not force: raise InitDBException(f"Cannot remove existing user or database without --force flag specified.")

    if user_exists and db_init_username != db_username: # if `db_init_username` is used as app user, don't delete it
        print(f"Deleting existing role '{db_username}'...")
        # Close existing connections of `db_username`
        cursor.execute(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.usename = '{db_username}';
        """)
        print("Closed existing connections.")

        # Connect to each database, except for default => reassign objects owned by `db_username` to `db_init_username` and drop all privileges of `db_username`
        # https://dba.stackexchange.com/questions/155332/find-objects-linked-to-a-postgresql-role
        cursor.execute(f"SELECT datname FROM pg_catalog.pg_database WHERE datname NOT IN ('template0', '{db_init_database}')")
        for (database_name, ) in cursor.fetchall():
            database_cursor = connect(host=db_config["db_host"], port=db_config["db_port"], database=database_name,
                user=db_init_username, password=db_config["db_init_password"])
            database_cursor.execute(f"""REASSIGN OWNED BY {db_username} TO {db_init_username}; DROP OWNED BY {db_username};""")
            disconnect(database_cursor)
        print(f"Finished clearing ownership & privileges in existing databases.")
        
        # Drop user
        cursor.execute(f"DROP ROLE {db_username};")
        print(f"Successfully deleted existing role '{db_username}'.")
    
    if database_exists:
        print(f"Deleting existing database '{db_database}'...")
        # Close existing connections to the database
        cursor.execute(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{db_database}'
                        AND pid <> pg_backend_pid();
        """)
        print(f"Closed existing connections to the database.")

        # Drop database
        cursor.execute(f"DROP DATABASE {db_database};")
        print(f"Successfully deleted existing database '{db_database}'.")


def create_user(cursor, user, password):
    cursor.execute(f"CREATE ROLE {user} PASSWORD '{password}' LOGIN;")
    print("Finished creating the user.")


def create_db(cursor, db_name, db_owner):
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
    print("Running migrations as superuser...")
    cursor = connect(host=db_config["db_host"], port=db_config["db_port"], database=db_config["db_database"],
                                user=db_config["db_init_username"], password=db_config["db_init_password"])
    try:
        # Create extension for password storing
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    finally:
        if type(cursor) == CursorClass:
            disconnect(cursor)
        print("Fihished running migrations as superuser.")


def migrate(config_file = None, test_uuid = None):
    print("Running Alembic migrations...")
    # Set current working directory
    cwd = os.getcwd()
    alembic_dir = os.path.dirname(__file__)
    os.chdir(alembic_dir)

    # Run revision command
    alembic_args = []
    if config_file is not None: alembic_args.extend(["-x", f'app_config_path="{config_file}"'])
    if test_uuid is not None: alembic_args.extend(["-x", f'test_uuid="{test_uuid}"'])
    alembic_args.extend(["upgrade", "head"])
    alembic.config.main(argv=alembic_args)

    # Restore current working directory
    os.chdir(cwd)
    print("Finished running Alembic migrations.")
