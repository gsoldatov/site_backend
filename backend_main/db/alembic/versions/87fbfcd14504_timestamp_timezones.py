"""Timestamp timezones

Revision ID: 87fbfcd14504
Revises: 7c8e91045b4d
Create Date: 2024-12-09 12:47:51.958585

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87fbfcd14504'
down_revision = '7c8e91045b4d'
branch_labels = None
depends_on = None


non_nullable_fields = [
    ("users", "registered_at"),
    ("sessions", "expiration_time"),
    ("login_rate_limits", "cant_login_until"),
    ("tags", "created_at"), ("tags", "modified_at"),
    ("objects", "created_at"), ("objects", "modified_at"),
    ("searchables", "modified_at")
]

nullable_fields = [("objects", "feed_timestamp")]


def upgrade():
    # Non-nullable fields
    for t, c in non_nullable_fields:
        # Add a new column with timezone, populate it with existing values, then replace the old column
        op.add_column(t, sa.Column(f"{c}_with_tz", sa.DateTime(timezone=True)))
        op.execute(f"UPDATE {t} SET {c}_with_tz = {c} AT TIME ZONE 'UTC'")
        op.drop_column(t, c)
        op.alter_column(t, f"{c}_with_tz", new_column_name=c, nullable=False)
    
    # Nullable fields
    for t, c in nullable_fields:
        # Add a new column with timezone, populate it with existing values, then replace the old column
        op.add_column(t, sa.Column(f"{c}_with_tz", sa.DateTime(timezone=True)))
        op.execute(f"UPDATE {t} SET {c}_with_tz = {c} AT TIME ZONE 'UTC'")
        op.drop_column(t, c)
        op.alter_column(t, f"{c}_with_tz", new_column_name=c)

    


def downgrade():
    # Non-nullable fields
    for t, c in non_nullable_fields:
        # Add a new column without timezone, populate it with existing values, then replace the old column
        op.add_column(t, sa.Column(f"{c}_no_tz", sa.DateTime(timezone=False)))
        op.execute(f"UPDATE {t} SET {c}_no_tz = ({c} AT TIME ZONE 'UTC')::TIMESTAMP")
        op.drop_column(t, c)
        op.alter_column(t, f"{c}_no_tz", new_column_name=c, nullable=False)
    
    # Non-nullable fields
    for t, c in nullable_fields:
        # Add a new column without timezone, populate it with existing values, then replace the old column
        op.add_column(t, sa.Column(f"{c}_no_tz", sa.DateTime(timezone=False)))
        op.execute(f"UPDATE {t} SET {c}_no_tz = ({c} AT TIME ZONE 'UTC')::TIMESTAMP")
        op.drop_column(t, c)
        op.alter_column(t, f"{c}_no_tz", new_column_name=c)
