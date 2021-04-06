from sqlalchemy import (
    MetaData, Table, Column, ForeignKey, Index, text,
    DateTime, Integer, String, Text, Boolean
)
from sqlalchemy.schema import FetchedValue

def get_tables(config):
    meta = MetaData(schema = config["db"]["db_schema"])

    return {
        "tags": Table(
            "tags", 
            meta,
            Column("tag_id", Integer, primary_key = True, server_default = FetchedValue()),
            Column("created_at", DateTime, nullable = False),
            Column("modified_at", DateTime, nullable = False),
            Column("tag_name", String(255), nullable = False),
            Column("tag_description", Text),
            Index("lowered_tag_name", text("lower(tag_name)"), unique = True)
        ),
    
        "objects": Table(
            "objects", 
            meta,
            Column("object_id", Integer, primary_key = True, server_default = FetchedValue()),
            Column("object_type", String(32), nullable = False),
            Column("created_at", DateTime, nullable = False),
            Column("modified_at", DateTime, nullable = False),
            Column("object_name", String(255), nullable = False),
            Column("object_description", Text),
            Index("object_type_index", "object_type")
        ),

        "objects_tags": Table(
            "objects_tags", 
            meta,
            Column("tag_id", Integer, ForeignKey("tags.tag_id", ondelete = "CASCADE")),
            Column("object_id", Integer, ForeignKey("objects.object_id", ondelete = "CASCADE")),
            Index("objects_tags_index", "object_id", "tag_id", unique = True),
        ),

        "links": Table(
            "links", 
            meta,
            Column("object_id", Integer, ForeignKey("objects.object_id", ondelete = "CASCADE"), unique = True),
            Column("link", Text, nullable = False)
        ),

        "markdown": Table(
            "markdown", 
            meta,
            Column("object_id", Integer, ForeignKey("objects.object_id", ondelete = "CASCADE"), unique = True),
            Column("raw_text", Text, nullable = False)
        ),

        "to_do_lists": Table(
            "to_do_lists",
            meta,
            Column("object_id", Integer, ForeignKey("objects.object_id", ondelete = "CASCADE"), unique = True),
            Column("sort_type", String(32), nullable = False)
        ),

        "to_do_list_items": Table(
            "to_do_list_items",
            meta,
            Column("object_id", Integer, ForeignKey("to_do_lists.object_id", ondelete = "CASCADE")),
            Column("item_number", Integer, nullable = False),
            Column("item_state", String(32), nullable = False),
            Column("item_text", Text),
            Column("commentary", Text),
            Column("indent", Integer, nullable = False),
            Column("is_expanded", Boolean, nullable = False)
        )
    }
