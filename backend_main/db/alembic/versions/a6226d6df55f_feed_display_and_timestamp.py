""" "Feed display and timestamp"

Revision ID: a6226d6df55f
Revises: b790f463f46e
Create Date: 2021-12-04 11:51:12.822035

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6226d6df55f'
down_revision = 'b790f463f46e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('objects', sa.Column('display_in_feed', sa.Boolean()))
    op.execute("UPDATE objects SET display_in_feed = TRUE")
    op.alter_column('objects', 'display_in_feed', nullable=False)

    op.add_column('objects', sa.Column('feed_timestamp', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('objects', 'feed_timestamp')
    op.drop_column('objects', 'display_in_feed')
