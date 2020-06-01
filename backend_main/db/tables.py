from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
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
            Column("tag_name", String(255), nullable = False, unique = True),
            Column("tag_description", Text)
        ),
    
        "objects": Table(
            "objects", 
            meta,
            Column("object_id", Integer, primary_key = True, server_default = FetchedValue()),
            Column("created_at", DateTime, nullable = False),
            Column("modified_at", DateTime, nullable = False),
            Column("object_name", String(255), nullable = False, unique = True),
            Column("object_description", Text)
        ),

        "objects_tags_link": Table(
            "objects_tags_link", 
            meta,
            Column("tag_id", Integer, ForeignKey("tags.tag_id")),
            Column("object_id", Integer, ForeignKey("objects.object_id"))
        ),

        "url_links": Table(
            "url_links", 
            meta,
            Column("object_id", Integer, ForeignKey("objects.object_id")),
            Column("link", Text, nullable = False)
        )
    }
