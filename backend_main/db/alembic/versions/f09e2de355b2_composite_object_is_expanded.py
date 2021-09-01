""" "Composite object is_expanded"

Revision ID: f09e2de355b2
Revises: 7f3a49a733c7
Create Date: 2021-06-24 17:49:48.523175

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f09e2de355b2'
down_revision = '7f3a49a733c7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('composite', sa.Column('is_expanded', sa.Boolean()))      # Populate column with default values, then set it non-nullable
    op.execute('UPDATE composite SET is_expanded=TRUE')
    op.alter_column('composite', 'is_expanded', nullable=False)


def downgrade():
    op.drop_column('composite', 'is_expanded')
