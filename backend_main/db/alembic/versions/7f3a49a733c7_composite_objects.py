""" "Composite objects"

Revision ID: 7f3a49a733c7
Revises: 987f81c7b064
Create Date: 2021-05-02 12:43:30.470132

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f3a49a733c7'
down_revision = '987f81c7b064'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('composite',
    sa.Column('object_id', sa.Integer(), nullable=True),
    sa.Column('subobject_id', sa.Integer(), nullable=True),
    sa.Column('row', sa.Integer(), nullable=False),
    sa.Column('column', sa.Integer(), nullable=False),
    sa.Column('selected_tab', sa.Integer(), nullable=False),
    # sa.ForeignKeyConstraint(['object_id'], ['public.objects.object_id'], ondelete='CASCADE'),
    # sa.ForeignKeyConstraint(['subobject_id'], ['public.objects.object_id'], ondelete='CASCADE'),
    schema='public'
    )
    
    op.create_foreign_key(op.f('fk_composite_object_id_objects'), 'composite', 'objects', ['object_id'], ['object_id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_composite_subobject_id_objects'), 'composite', 'objects', ['subobject_id'], ['object_id'], source_schema='public', referent_schema='public', ondelete='CASCADE')


def downgrade():
    op.drop_constraint(op.f('fk_composite_subobject_id_objects'), 'composite', schema='public', type_='foreignkey')
    op.drop_constraint(op.f('fk_composite_object_id_objects'), 'composite', schema='public', type_='foreignkey')

    op.drop_table('composite', schema='public')
