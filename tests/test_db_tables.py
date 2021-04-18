"""
db/init_db.py tests
"""
import os, sys
import shutil

import pytest
from sqlalchemy import Table

sys.path.insert(0, os.path.join(sys.path[0], '..'))
from backend_main.db.tables import get_tables


def test_get_tables(config, db_cursor):
    """
    Checks that SQLAlchemy objects match the state of the database after migrations applied to it.
    """
    schema = config["db"]["db_schema"]

    # Get SQL Alchemy tables
    sa_tables = get_tables(config)[0]

    # Check if SA and DB tables match + check that all objects returned by get_tables belong to SQLAlchemy Table class
    db_cursor.execute(f"SELECT tablename FROM pg_tables WHERE schemaname = '{schema}' AND tablename <> 'alembic_version'")
    db_tables = [r[0] for r in db_cursor.fetchall()]

    for t in sa_tables:
        if t not in db_tables:
            pytest.fail(f"'{t}' table is defined as an SQLAlchemy object, but not present in the database.")
        
        if type(sa_tables[t]) != Table:
            pytest.fail(f"'{t}' table is not an SQLAlchemy Table instance.")
    
    for t in db_tables:
        if t not in sa_tables:
            pytest.fail(f"'{t}' table is defined in the database, but not as an SQLAlchemy object.")
    
    # Get db table columns
    db_cursor.execute(f"""
                        SELECT table_name, column_name 
                        FROM information_schema.columns
                        WHERE table_schema = '{schema}' AND table_name <> 'alembic_version'
                        """
    )
    db_column_names = {}

    for row in db_cursor.fetchall():
        table, column_name = row[0], row[1]
        
        if not db_column_names.get(table):
            db_column_names[table] = []
        
        db_column_names[table].append(column_name)
    
    # Get SA table columns
    sa_column_names = {}

    for table in sa_tables:
        sa_column_names[table] = []

        for column in sa_tables[table].c:
            sa_column_names[table].append(column.name)

    # Check if SA and DB column names match
    for table in sa_tables:
        # SA in DB
        for column in sa_column_names[table]:
            if column not in db_column_names[table]:
                pytest.fail(f"SQLAlchemy column '{table}.{column}' is not defined in the database.")

        # DB in SA
        for column in db_column_names[table]:
            if column not in sa_column_names[table]:
                pytest.fail(f"Database column '{table}.{column}' is not defined in the SQLAlchemy table.")


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
