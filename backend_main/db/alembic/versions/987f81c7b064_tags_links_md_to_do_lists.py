""" "Tags, links, md, to-do lists"

Revision ID: 987f81c7b064
Revises: 
Create Date: 2021-04-17 12:25:31.010898

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import FetchedValue


# revision identifiers, used by Alembic.
revision = '987f81c7b064'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('tags',
    sa.Column('tag_id', sa.Integer(), server_default=FetchedValue(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('tag_name', sa.String(length=255), nullable=False),
    sa.Column('tag_description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('tag_id')
    )
    op.create_index('ix_tag_name_lowered', 'tags', [sa.text('lower(tag_name)')], unique=True) # added manually
    op.execute("ALTER TABLE tags ALTER tag_id ADD GENERATED BY DEFAULT AS IDENTITY")

    op.create_table('objects',
    sa.Column('object_id', sa.Integer(), server_default=FetchedValue(), nullable=False),
    sa.Column('object_type', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('object_name', sa.String(length=255), nullable=False),
    sa.Column('object_description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('object_id')
    )
    op.create_index('ix_object_type', 'objects', ['object_type'], unique=False)
    op.execute("ALTER TABLE objects ALTER object_id ADD GENERATED BY DEFAULT AS IDENTITY")
    
    op.create_table('objects_tags',
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.Column('object_id', sa.Integer(), nullable=False)
    )
    op.create_foreign_key(op.f('fk_objects_tags_object_id_objects'), 'objects_tags', 'objects', ['object_id'], ['object_id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_objects_tags_tag_id_tags'), 'objects_tags', 'tags', ['tag_id'], ['tag_id'], ondelete='CASCADE')
    op.create_index('ix_object_id_tag_id', 'objects_tags', ['object_id', 'tag_id'], unique=True)

    op.create_table('links',
    sa.Column('object_id', sa.Integer(), nullable=True),
    sa.Column('link', sa.Text(), nullable=False),
    sa.UniqueConstraint('object_id')
    )
    op.create_foreign_key(op.f('fk_links_object_id_objects'), 'links', 'objects', ['object_id'], ['object_id'], ondelete='CASCADE')

    op.create_table('markdown',
    sa.Column('object_id', sa.Integer(), nullable=True),
    sa.Column('raw_text', sa.Text(), nullable=False),
    sa.UniqueConstraint('object_id')
    )
    op.create_foreign_key(op.f('fk_markdown_object_id_objects'), 'markdown', 'objects', ['object_id'], ['object_id'], ondelete='CASCADE')
    
    op.create_table('to_do_lists',
    sa.Column('object_id', sa.Integer(), nullable=True),
    sa.Column('sort_type', sa.String(length=32), nullable=False),
    sa.UniqueConstraint('object_id')
    )
    op.create_foreign_key(op.f('fk_to_do_lists_object_id_objects'), 'to_do_lists', 'objects', ['object_id'], ['object_id'], ondelete='CASCADE')

    op.create_table('to_do_list_items',
    sa.Column('object_id', sa.Integer(), nullable=True),
    sa.Column('item_number', sa.Integer(), nullable=False),
    sa.Column('item_state', sa.String(length=32), nullable=False),
    sa.Column('item_text', sa.Text(), nullable=True),
    sa.Column('commentary', sa.Text(), nullable=True),
    sa.Column('indent', sa.Integer(), nullable=False),
    sa.Column('is_expanded', sa.Boolean(), nullable=False)
    )
    op.create_foreign_key(op.f('fk_to_do_list_items_object_id_to_do_lists'), 'to_do_list_items', 'to_do_lists', ['object_id'], ['object_id'], ondelete='CASCADE')


def downgrade():
    op.drop_constraint(op.f('fk_to_do_list_items_object_id_to_do_lists'), 'to_do_list_items', type_='foreignkey')
    op.drop_table('to_do_list_items')

    op.drop_constraint(op.f('fk_to_do_lists_object_id_objects'), 'to_do_lists', type_='foreignkey')
    op.drop_table('to_do_lists')

    op.drop_constraint(op.f('fk_markdown_object_id_objects'), 'markdown', type_='foreignkey')
    op.drop_table('markdown')

    op.drop_constraint(op.f('fk_links_object_id_objects'), 'links', type_='foreignkey')
    op.drop_table('links')

    op.drop_index('ix_object_id_tag_id', table_name='objects_tags')
    op.drop_constraint(op.f('fk_objects_tags_tag_id_tags'), 'objects_tags', type_='foreignkey')
    op.drop_constraint(op.f('fk_objects_tags_object_id_objects'), 'objects_tags', type_='foreignkey')
    op.drop_table('objects_tags')

    op.drop_index('ix_object_type', table_name='objects')
    op.drop_table('objects')

    op.drop_index('ix_tag_name_lowered', table_name='tags') # added manually
    op.drop_table('tags')
