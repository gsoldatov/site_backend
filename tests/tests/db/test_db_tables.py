"""
db/init_db.py tests
"""
import os, sys

import pytest
from sqlalchemy import Table

sys.path.insert(0, os.path.join(sys.path[0], "../" * 3))
from backend_main.db.tables import get_tables
from backend_main.db.types import AppTables
from tests.util import run_pytest_tests


def test_get_tables(db_cursor):
    """
    Checks that SQLAlchemy objects match the state of the database after migrations applied to it.
    """
    # Get SQL Alchemy tables
    sa_tables = get_tables()[0].__dict__

    # Check if SA and DB tables match + check that all objects returned by get_tables belong to SQLAlchemy Table class
    db_cursor.execute(f"SELECT tablename FROM pg_tables WHERE schemaname = current_schema() AND tablename <> 'alembic_version'")
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
                        WHERE table_schema = current_schema() AND table_name <> 'alembic_version'
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


def test_table_type_stubs():
    # Check if stub tables match tables
    sa_tables = get_tables()[0]
    sa_table_names = set(sa_tables.__dict__)
    stub_table_names = set(AppTables.__annotations__)
    
    missing_stub_table_names = sa_table_names.difference(stub_table_names)
    assert len(missing_stub_table_names) == 0, f"Table type stubs for {missing_stub_table_names} are missing."

    # Check if non-existing tables are present in type stubs
    non_existing_table_names = stub_table_names.difference(sa_table_names)
    assert len(non_existing_table_names) == 0, f"Table type stubs contain non-existing tables {non_existing_table_names}."

    # Check if type stubs contain correct columns for each table
    for table_name in sa_table_names:
        # Get SQLAlchemy & stub column names
        sa_table = getattr(sa_tables, table_name)
        sa_table_column_names = set(col.name for col in sa_table.c.values())

        stub_table_class = AppTables.__annotations__[table_name]
        assert "c" in stub_table_class.__annotations__, f"Stub {stub_table_class} does not have 'c' attribute."
        stub_table_column_names = set(stub_table_class.__annotations__["c"].__annotations__)

        # Check if stubs have required columns
        missing_column_names = sa_table_column_names.difference(stub_table_column_names)
        assert len(missing_column_names) == 0, f"Stubs for table {table_name} are missing columns {missing_column_names}."

        # Check if stubs don't have non-existing columns
        non_existing_columns = stub_table_column_names.difference(sa_table_column_names)
        assert len(non_existing_columns) == 0, f"Stubs for table {table_name} have non-existing columns {non_existing_columns}."


if __name__ == "__main__":
    run_pytest_tests(__file__)
