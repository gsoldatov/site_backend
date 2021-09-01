from sqlalchemy import (
    MetaData, Table, Column, ForeignKey, Index, text,
    DateTime, Integer, String, Text, Boolean
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import FetchedValue

def get_tables(config):
    """ Return a dictionary with SA tables and a metadata object. """
    meta = MetaData(schema = config["db"]["db_schema"],
        naming_convention={
        "ix": "ix_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

    return {
        # App settings
        "settings": Table(
            "settings",
            meta,
            Column("setting_name", String(255), primary_key=True),
            Column("setting_value", String(255))
        ),

        # Users, sessions and log in rate limiting
        "users": Table(
            "users",
            meta,
            Column("user_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("login", String(255), nullable=False, unique=True),
            Column("password", Text, nullable=False),
            Column("username", String(255), nullable=False, unique=True),
            Column("user_level", String(16), nullable=False),
            Column("can_edit_objects", Boolean, nullable=False)
        ),

        "sessions": Table(
            "sessions",
            meta,
            Column("user_id", Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
            Column("access_token", Text, nullable=False),
            Column("expiration_time", DateTime, nullable=False)
        ),

        "login_rate_limits": Table(
            "login_rate_limits",
            meta,
            Column("ip_address", postgresql.INET, primary_key=True),
            Column("failed_login_attempts", Integer, nullable=False),
            Column("cant_login_until", DateTime, nullable=False)
        ),

        # Objects and tags
        "tags": Table(
            "tags", 
            meta,
            Column("tag_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("created_at", DateTime, nullable=False),
            Column("modified_at", DateTime, nullable=False),
            Column("tag_name", String(255), nullable=False),
            Column("tag_description", Text),
            Index("ix_tag_name_lowered", text("lower(tag_name)"), unique=True),

            Column("is_published", Boolean, nullable=False)
        ),
    
        "objects": Table(
            "objects", 
            meta,
            Column("object_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("object_type", String(32), nullable=False, index=True),
            Column("created_at", DateTime, nullable=False),
            Column("modified_at", DateTime, nullable=False),
            Column("object_name", String(255), nullable=False),
            Column("object_description", Text),
            
            Column("owner_id", Integer, ForeignKey("users.user_id", onupdate="CASCADE", ondelete="SET NULL"), nullable=False),
            Column("is_published", Boolean, nullable=False)
        ),

        "objects_tags": Table(
            "objects_tags", 
            meta,
            Column("tag_id", Integer, ForeignKey("tags.tag_id", ondelete="CASCADE"), nullable=False),
            Column("object_id", Integer, ForeignKey("objects.object_id", ondelete="CASCADE"), nullable=False),
            Index("ix_object_id_tag_id", "object_id", "tag_id", unique=True),
        ),

        "links": Table(
            "links", 
            meta,
            Column("object_id", Integer, ForeignKey("objects.object_id", ondelete="CASCADE"), unique=True),
            Column("link", Text, nullable=False)
        ),

        "markdown": Table(
            "markdown", 
            meta,
            Column("object_id", Integer, ForeignKey("objects.object_id", ondelete="CASCADE"), unique=True),
            Column("raw_text", Text, nullable=False)
        ),

        "to_do_lists": Table(
            "to_do_lists",
            meta,
            Column("object_id", Integer, ForeignKey("objects.object_id", ondelete="CASCADE"), unique=True),
            Column("sort_type", String(32), nullable=False)
        ),

        "to_do_list_items": Table(
            "to_do_list_items",
            meta,
            Column("object_id", Integer, ForeignKey("to_do_lists.object_id", ondelete = "CASCADE")),
            Column("item_number", Integer, nullable=False),
            Column("item_state", String(32), nullable=False),
            Column("item_text", Text),
            Column("commentary", Text),
            Column("indent", Integer, nullable=False),
            Column("is_expanded", Boolean, nullable=False)
        ),

        "composite": Table(
            "composite",
            meta,
            Column("object_id", Integer, ForeignKey("objects.object_id", ondelete="CASCADE")),
            Column("subobject_id", Integer, ForeignKey("objects.object_id", ondelete="CASCADE")),
            Column("row", Integer, nullable=False),
            Column("column", Integer, nullable=False),
            Column("selected_tab", Integer, nullable=False),
            Column("is_expanded", Boolean, nullable=False)
        )
    } \
    , meta
