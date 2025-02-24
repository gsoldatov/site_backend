# General
A backend API for a [personal blog/notebook](https://github.com/gsoldatov/site_frontend) implemented, using Aiohttp & Postgresql.

[Deployment](https://github.com/gsoldatov/site_deployment) repo contains a set of Ansible playbooks for deploying this repo and frontend.


# Development
## Setup
The following must be done before app can be run:
1) Creating a virtual env & installing dependencies from `requirements.txt`;
2) Adding a development app config at `backend_main/config.json` (`backend_main/config.json.sample` can be used as a template);
3) Ensuring a Postgresql 14+ instance exists and is running with the settings specified in the config file (location, default database & superuser).
4) creating a dev database:
    ```bash
    python -m backend_main.db
    ```

## Running App
```bash
python -m backend_main
```

## Database Management
### Replacing Existing Database with a New One
```bash
python -m backend_main.db --force
```

### Creating An Alembic Revision
```bash
python -m backend_main.db --revision --message "<Migration message>"

# or
cd backend_main/db
alembic revision --autogenerate -m "<revision message>"
```

### Migrating to the Latest Revision
```bash
python -m backend_main.db --migrate

# or
cd backend_main/db
alembic upgrade head 
```

### Migrating to Other Revisions
```bash
# `alembic` must be invoked from the `db` dir
cd backend_main/db

# Apply migrations to the database up to <revision hash>
alembic upgrade <revision hash>

# Downgrade database to <revision hash
alembic downgrade <revision hash>
```


# Testing
## Setup
Before tests can be run, a separate app configuration must be put at `<project_root>/tests/test_config.json`. Differences from dev configuration should include setting all logging modes to `off` and `debug` to True. `use_forwarded` can be set to True, as well.

## `tests` Module
`tests` module handles fixture cleanup and invokes pytest with additional plugins.

```bash
source venv/bin/activate
python -m tests [<additional pytest args>]
```

### `tests` Module Usage Examples
```bash
# Runs all tests
python -m tests
```

Any CLI args given to `tests` module will be passed to the invoked `pytest` command.

Tests from specific files & dirs can be performed by passing their paths relative to `<project_root>/tests/tests` directory:

```bash
# Run a single file `test_config.py`
python -m tests modules/test_config.py

# Run all tests in the `routes/objects` dir
python -m tests routes/objects

# Run tests from several files/dirs
python -m tests modules/test_config.py routes/objects
```

## Running Test Files
Each test file can be executed directly in order to run all its tests.
