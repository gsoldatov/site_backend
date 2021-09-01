""" "Users and auth"

Revision ID: 4c0477896c90
Revises: f09e2de355b2
Create Date: 2021-08-29 12:52:30.874486

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import FetchedValue
from sqlalchemy.dialects import postgresql

from alembic import context
from backend_main.config import get_config

# revision identifiers, used by Alembic.
revision = '4c0477896c90'
down_revision = 'f09e2de355b2'
branch_labels = None
depends_on = None

# Get Alembic config => read app config path from it => read app config
config = context.config

app_config_path = context.get_x_argument(as_dictionary=True).get("app_config_path")
if type(app_config_path) == str:
    app_config_path = app_config_path.replace('"', '')
app_config = get_config(app_config_path)


def upgrade():
    # New tables
    op.create_table('settings',
    sa.Column('setting_name', sa.String(length=255), nullable=False),
    sa.Column('setting_value', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('setting_name', name=op.f('pk_settings')),
    schema='public'
    )
    op.create_table('users',
    sa.Column('user_id', sa.Integer(), server_default=FetchedValue(), nullable=False),
    sa.Column('login', sa.String(length=255), nullable=False),
    sa.Column('password', sa.Text(), nullable=False),
    sa.Column('username', sa.String(length=255), nullable=False),
    sa.Column('user_level', sa.String(length=16), nullable=False),
    sa.Column('can_edit_objects', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_users')),
    sa.UniqueConstraint('login', name=op.f('uq_users_login')),
    sa.UniqueConstraint('username', name=op.f('uq_users_username')),
    schema='public'
    )
    op.execute("ALTER TABLE users ALTER user_id ADD GENERATED BY DEFAULT AS IDENTITY")

    op.create_table('sessions',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('access_token', sa.Text(), nullable=False),
    sa.Column('expiration_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['public.users.user_id'], name=op.f('fk_sessions_user_id_users'), ondelete='CASCADE'),
    schema='public'
    )
    op.create_table('login_rate_limits',
    sa.Column('ip_address', postgresql.INET(), nullable=False),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
    sa.Column('cant_login_until', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('ip_address', name=op.f('pk_login_rate_limits')),
    schema='public'
    )

    # Add app setting
    op.execute("INSERT INTO settings VALUES ('registration_allowed', 'FALSE')")

    # Create extension for password storing
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Add default user
    login = app_config["default_user"]["login"]
    password = app_config["default_user"]["password"]
    username = app_config["default_user"]["username"]
    op.execute(f"""INSERT INTO users (login, password, username, user_level, can_edit_objects)
                   VALUES ('{login}', crypt('{password}', gen_salt('bf')), '{username}', 'admin', TRUE)""")

    # Objects table
    op.add_column('objects', sa.Column('is_published', sa.Boolean()))
    op.execute('UPDATE objects SET is_published=FALSE')
    op.alter_column('objects', 'is_published', nullable=False)

    op.add_column('objects', sa.Column('owner_id', sa.Integer()))
    conn = op.get_bind()
    default_user_id = conn.execute("SELECT user_id FROM users").fetchone()[0]
    op.execute(f'UPDATE objects SET owner_id={default_user_id}')
    op.alter_column('objects', 'owner_id', nullable=False)

    op.create_foreign_key(op.f('fk_objects_owner_id_users'), 'objects', 'users', ['owner_id'], ['user_id'], source_schema='public', referent_schema='public', onupdate='CASCADE', ondelete='SET NULL')

    # Tags table
    op.add_column('tags', sa.Column('is_published', sa.Boolean()))
    op.execute('UPDATE tags SET is_published=TRUE')
    op.alter_column('tags', 'is_published', nullable=False)


def downgrade():
    op.drop_column('tags', 'is_published')

    op.drop_constraint(op.f('fk_objects_owner_id_users'), 'objects', schema='public', type_='foreignkey')
    op.drop_column('objects', 'owner_id')
    op.drop_column('objects', 'is_published')
    
    op.drop_table('login_rate_limits', schema='public')
    op.drop_table('sessions', schema='public')
    op.drop_table('users', schema='public')
    op.drop_table('settings', schema='public')
