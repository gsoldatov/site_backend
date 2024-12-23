import os

import psycopg2
from psycopg2.extensions import cursor as CursorClass
import alembic.config

from backend_main.logging.loggers.db import get_logger

from backend_main.types.app import Config


class InitDBException(Exception):
    pass


def connect(
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ):
    connection = psycopg2.connect(host=host, port=port, database=database, \
                            user=user, password=password)
    connection.set_session(autocommit=True)
    return connection.cursor()


def disconnect(cursor: CursorClass | None):
    if cursor:
        if cursor.connection:
            cursor.close()
            cursor.connection.close()


def drop_user_and_db(config: Config, cursor: CursorClass, force: bool):
    """
    Removes user and database with `db_username` and `db_database` names specified in the config respectively, if `force` flag is true.
    Checks all existing databases, reassigns all owned objects to default user and removes all privileges granted to default user.
    After that, deletes the user and the database.
    """
    # Get logger
    logger = get_logger("drop_user_and_db", config)

    # Validate `db_database` and `db_username` values
    logger.info("Deleting existing user and database...")
    db_init_username, db_init_database = config.db.db_init_username.value, config.db.db_init_database.value
    db_username, db_database = config.db.db_username.value, config.db.db_database.value
    
    if db_init_database == db_database: raise InitDBException("db_init_database and db_database cannot be equal.")    
    if db_database == "template0": raise InitDBException("db_database cannot be equal to 'template0'.")
    logger.info("Finished validating app user and database.")

    # Get user and database
    cursor.execute(f"SELECT usename FROM pg_user WHERE usename = '{db_username}'")
    user_exists = cursor.fetchone() is not None
    cursor.execute(f"SELECT datname FROM pg_catalog.pg_database WHERE datname = '{db_database}'")
    database_exists = cursor.fetchone() is not None

    # If none exists, return
    logger.info("Found existing app user." if user_exists else "App user does not exist.")
    logger.info("Found existing app database." if database_exists else "App database does not exist.")
    if not (user_exists or database_exists):
        logger.info("App user and database do not exist, exiting.")
        return
    
    # If at least one exists, and force flag is not provided, raise InitDBException
    if not force: raise InitDBException(f"Cannot remove existing user or database without --force flag specified.")

    if user_exists and db_init_username != db_username: # if `db_init_username` is used as app user, don't delete it
        logger.info("Deleting existing app user...")
        # Close existing connections of `db_username`
        cursor.execute(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.usename = '{db_username}';
        """)
        logger.info("Closed existing app user connections.")

        # Connect to each database, except for default => reassign objects owned by `db_username` to `db_init_username` and drop all privileges of `db_username`
        # https://dba.stackexchange.com/questions/155332/find-objects-linked-to-a-postgresql-role
        cursor.execute(f"SELECT datname FROM pg_catalog.pg_database WHERE datname NOT IN ('template0', '{db_init_database}')")
        for (database_name, ) in cursor.fetchall():
            database_cursor = connect(host=config.db.db_host, port=config.db.db_port, database=database_name,
                user=db_init_username, password=config.db.db_init_password.value)
            database_cursor.execute(f"""REASSIGN OWNED BY {db_username} TO {db_init_username}; DROP OWNED BY {db_username};""")
            disconnect(database_cursor)
        logger.info("Cleared app user ownership & privileges in existing databases.")
        
        # Drop user
        cursor.execute(f"DROP ROLE {db_username};")
        logger.info("Finished deleting app user.")
    
    if database_exists:
        logger.info("Deleting existing app database...")

        # Close existing connections to the database
        cursor.execute(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{db_database}'
                        AND pid <> pg_backend_pid();
        """)
        logger.info("Closed existing connections to app database.")

        # Drop database
        cursor.execute(f"DROP DATABASE {db_database};")
        logger.info("Finished deleting app database.")


def create_user(config: Config, cursor: CursorClass):
    logger = get_logger("create_user", config)
    logger.info("Creating app user...")
    cursor.execute(f"""CREATE ROLE {config.db.db_username.value} PASSWORD '{config.db.db_password.value}' LOGIN;""")
    logger.info("Finished creating app user.")


def create_db(config: Config, cursor: CursorClass):
    logger = get_logger("create_database", config)
    logger.info("Creating app database...")
    cursor.execute(f"""CREATE DATABASE {config.db.db_database.value} ENCODING 'UTF-8' OWNER {config.db.db_username.value} TEMPLATE template0;""")
    logger.info("Finished creating app database.")


def revision(config: Config, message: CursorClass):
    # Get logger
    logger = get_logger("revision", config)

    # Set current working directory
    cwd = os.getcwd()
    alembic_dir = os.path.dirname(__file__)
    os.chdir(alembic_dir)

    # Run revision command
    logger.info("Running alembic revision command...")
    alembic_args = ["revision", "--autogenerate", f'-m "{message}"']
    alembic.config.main(argv=alembic_args)

    # Restore current working directory
    os.chdir(cwd)
    logger.info("Revision command finished running.")


def migrate_as_superuser(config: Config):
    """Additional migration commands which require as superuser privilege."""
    # Get logger
    logger = get_logger("migrate_as_superuser", config)

    logger.info("Running migrations as superuser...")
    cursor = connect(host=config.db.db_host, port=config.db.db_port, database=config.db.db_database.value,
                            user=config.db.db_init_username.value, password=config.db.db_init_password.value)
    logger.info(f"Connected to the app database.")
    try:
        # Create extension for password storing
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        
        logger.info("Fihished running migrations as superuser.")
    finally:
        if type(cursor) == CursorClass:
            disconnect(cursor)
            logger.info(f"Disconnected from the app database.")


def migrate(config: Config, config_file: str | None = None, test_uuid: str | None = None):
    # Get logger
    logger = get_logger("migrate", config)

    logger.info("Running Alembic migrations...")
    # Set current working directory
    cwd = os.getcwd()
    alembic_dir = os.path.dirname(__file__)
    os.chdir(alembic_dir)

    # Run migrate command
    alembic_args = []
    if config_file is not None: alembic_args.extend(["-x", f'app_config_path="{config_file}"'])
    if test_uuid is not None: alembic_args.extend(["-x", f'test_uuid="{test_uuid}"'])
    alembic_args.extend(["upgrade", "head"])
    alembic.config.main(argv=alembic_args)

    # Restore current working directory
    os.chdir(cwd)
    logger.info("Finished running Alembic migrations.")
