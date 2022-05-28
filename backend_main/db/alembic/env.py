from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os, sys
root_folder = os.path.abspath(os.path.join(__file__, os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir))
sys.path.insert(0, root_folder)

import urllib.parse

from backend_main.config import get_config
from backend_main.db.tables import get_tables
from tests.util import get_test_name


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get app config
x_arguments = context.get_x_argument(as_dictionary=True)
app_config_path = x_arguments.get("app_config_path")
if app_config_path is not None:
    app_config_path = app_config_path.replace('"', '')
app_config = get_config(app_config_path)

# Modify app user & db names to match the ones created for the tests if `test_uuid` was passed
test_uuid = x_arguments.get("test_uuid")
if test_uuid is not None:
    test_uuid = test_uuid.replace('"', '')
    app_config["db"]["db_database"] = get_test_name(app_config["db"]["db_database"], test_uuid)
    app_config["db"]["db_username"] = get_test_name(app_config["db"]["db_username"], test_uuid)

# Set connection string
username = urllib.parse.quote(app_config["db"]["db_username"].value).replace("%", "%%") # encode special characters in username and password;
password = urllib.parse.quote(app_config["db"]["db_password"].value).replace("%", "%%") # after quoting, '%' chars must also be escaped to avoid "ValueError: invalid interpolation syntax" exception

config.set_main_option("sqlalchemy.url", f"postgresql://{username}:{password}"
                        f"@{app_config['db']['db_host']}:{app_config['db']['db_port']}/{app_config['db']['db_database'].value}")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name, disable_existing_loggers=False)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = get_tables()[1]

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
