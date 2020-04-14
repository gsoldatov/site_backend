"""
Database fixtures.
"""

import pytest
import psycopg2
import os
import shutil
import subprocess


__all__ = ["config", "init_db_cursor", "db_cursor", "migration_folder", "db_and_user", "migrate"]


@pytest.fixture(scope = "module")
def init_db_cursor(config):
    """
        psycopg2.Cursor object for creating and dropping test user and database.
    """
    db_config = config["db"]
    connection = psycopg2.connect(host = db_config["db_host"], port = db_config["db_port"], 
                    database = db_config["db_init_database"], user = db_config["db_init_username"], 
                    password = db_config["db_init_password"])
    connection.set_session(autocommit=True)
    cursor = connection.cursor()
    yield cursor
    cursor.close()
    connection.close()
 

@pytest.fixture(scope = "module")
def db_cursor(config, init_db_cursor, db_and_user):
    """
        Fixture factory for creating psycopg2.Cursor objects
        for performing queries against the test database.
    """
    def wrappee(apply_migrations = True):
        nonlocal _cursor

        if _cursor:
            return _cursor

        db_and_user(apply_migrations)

        db_config = config["db"]
        connection = psycopg2.connect(host = db_config["db_host"], port = db_config["db_port"], 
                        database = db_config["db_database"], user = db_config["db_username"], 
                        password = db_config["db_password"])
        connection.set_session(autocommit=True)
        _cursor = connection.cursor()
        return _cursor
    
    _cursor = None
    yield wrappee
    _cursor.close()
    _cursor.connection.close()


@pytest.fixture(scope = "module")
def migration_folder():
    """
    Fixture, which handles migration folder creation and deletion.
    """
    folder = os.path.dirname(os.path.abspath(__file__)) + "/test_migrations"
    if not os.path.exists(folder):
        os.mkdir(folder)
    
    with open(folder + "/V1__test_migration.sql", "w") as stream:
        stream.write("""
                    CREATE TABLE test (
                    id INT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE
                    );"""
        )
    yield folder
    shutil.rmtree(folder)


@pytest.fixture(scope = "module")
def db_and_user(config, init_db_cursor, migrate):
    """
        Fixture factory for creating temporary user and database.
    """
    def wrappee(apply_migrations = True):
        nonlocal _db_created

        if _db_created:
            return
        
        db_config = config["db"]
        init_db_cursor.execute(f"""DROP DATABASE IF EXISTS {config["db"]["db_database"]}""")
        init_db_cursor.execute(f"""DROP USER IF EXISTS {config["db"]["db_username"]}""")
        init_db_cursor.execute(f"""CREATE USER {config["db"]["db_username"]} PASSWORD \'{config["db"]["db_password"]}\' LOGIN;""")
        init_db_cursor.execute(f"""CREATE DATABASE {config["db"]["db_database"]} ENCODING 'UTF-8' OWNER {config["db"]["db_username"]} TEMPLATE template0;""")

        if apply_migrations:
            migrate()
        
        _db_created = True
    
    _db_created = False
    yield wrappee

    init_db_cursor.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{config["db"]["db_database"]}'
                    AND pid <> pg_backend_pid();
    """)
    init_db_cursor.execute(f"""DROP DATABASE IF EXISTS {config["db"]["db_database"]}""")
    init_db_cursor.execute(f"""DROP USER IF EXISTS {config["db"]["db_username"]}""")


@pytest.fixture(scope = "module")
def migrate(config):
    """
    Performs migrations on a test database.

    Returns a function which:
    - creates a temporary directory for migrations if it doesn't exist;
    - creates a flyway.conf file in the temporary directory from the provided config dict;
    - copies migration files from the specified directory into the temporary directory;
    - applies the migrations to the test database.
    Params:
        - cwd: working directory to run migrations from (default is "/migrations" subfolder in the test directory);
        - config: configiratuion dictionary with database params (default is config fixture);
        - copy_migrations_from: directory to copy migrations from (default is "../db/migrations")
    """

    def wrappee(cwd = None, cfg = config, copy_migrations_from = None):

        # Check and save params
        nonlocal _cwd

        if _cwd: # Migrate the db only once per test module
            return
        
        cwd = cwd or os.path.dirname(os.path.abspath(__file__)) + "/migrations"
        copy_migrations_from = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/db/migrations"
        
        _cwd = cwd

        # Create cwd folder if it doesn't exist
        if not os.path.exists(cwd):
            os.mkdir(cwd)
        
        # Create flyway.conf if it doesn't exist or raise and Exception
        conf_file = cwd + "/flyway.conf"
        if os.path.exists(conf_file):
            raise FileExistsError(f"flyway.conf file already exists in the {cwd}.")
            
        with open(conf_file, "w") as write_stream:
            write_stream.write("\n".join([
            f"flyway.url=jdbc:postgresql://{config['db']['db_host']}:{config['db']['db_port']}/{config['db']['db_database']}",
            f"flyway.user={config['db']['db_username']}",
            f"flyway.password={config['db']['db_password']}",
            f"flyway.schemas={config['db']['db_schema']}",
            f"flyway.locations=filesystem:./"
            ]))
        
        # Copy existing migrations into test folder
        for f in os.listdir(copy_migrations_from):
            abs_filename = os.path.join(copy_migrations_from, f)
            if os.path.isfile(abs_filename) and f.endswith(".sql"):
                shutil.copy(abs_filename, cwd)
        
        # Apply migrations
        p = subprocess.Popen(["flyway", "migrate"], shell = True, cwd = cwd)
        p.wait()
    
    _cwd = None

    try:
        yield wrappee
    finally:
        # Destroy migration folder during fixture teardown
        if _cwd:
            if os.path.exists(_cwd):
                shutil.rmtree(_cwd)

from fixtures_app import config
