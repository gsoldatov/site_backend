from sqlalchemy import (
    MetaData, Table, Column, ForeignKey, Index, text,
    DateTime, Integer, String, Text
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
            Column("object_type", Text, nullable = False),
            Column("created_at", DateTime, nullable = False),
            Column("modified_at", DateTime, nullable = False),
            Column("object_name", String(255), nullable = False, unique = True),
            Column("object_description", Text),
            Index("lowered_object_name", text("lower(object_name)"), unique = True),
            Index("object_type_index", "object_type")
        ),

        "objects_tags": Table(
            "objects_tags", 
            meta,
            Column("tag_id", Integer, ForeignKey("tags.tag_id")),
            Column("object_id", Integer, ForeignKey("objects.object_id")),
            Index("objects_tags_index", "object_id", "tag_id", unique = True),
        ),

        "links": Table(
            "links", 
            meta,
            Column("object_id", Integer, ForeignKey("objects.object_id")),
            Column("link", Text, nullable = False)
        )
    }
