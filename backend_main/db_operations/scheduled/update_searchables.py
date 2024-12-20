"""
Updates `searchables` table.
`mode` argument can be passed via CLI to determine, which data should be processed:
- "full" mode updates data for all existing tags and objects;
- "missing" (default mode) updates data for all tags and objects, which were not processed after last update.
"""
import argparse

from psycopg2 import connect

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(sys.path[0]))))

from backend_main.app.config import get_config
from backend_main.logging.loggers.scheduled import get_logger
from backend_main.db_operations.searchables import update_searchables


logger = None


def parse_args():
    # Parse CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", help="Which data is updated (full or with missing updates since last save).", choices=("full", "missing"))
    parser.set_defaults(mode="missing")
    return parser.parse_args()


def get_ids(conn, mode):
    try:
        cursor = conn.cursor()

        # full
        if mode == "full":
            cursor.execute("SELECT tag_id FROM tags")
            tag_ids = tuple(r[0] for r in cursor.fetchall())

            cursor.execute("SELECT object_id FROM objects")
            object_ids = tuple(r[0] for r in cursor.fetchall())

            return tag_ids, object_ids
        
        # missing
        else:
            cursor.execute("""
                SELECT 
                    tags.tag_id
                FROM tags
                LEFT JOIN searchables
                ON tags.tag_id = searchables.tag_id
                WHERE searchables.modified_at < tags.modified_at OR searchables.modified_at ISNULL
            """)
            tag_ids = tuple(r[0] for r in cursor.fetchall())

            cursor.execute("""
                SELECT 
                    objects.object_id
                FROM objects
                LEFT JOIN searchables
                ON objects.object_id = searchables.object_id
                WHERE searchables.modified_at < objects.modified_at OR searchables.modified_at ISNULL
            """)
            object_ids = tuple(r[0] for r in cursor.fetchall())

            return tag_ids, object_ids

    finally:
        if not cursor.closed: cursor.close()


def main(mode, config = None):
    try:
        # Get app config and logger
        config = config or get_config()
        global logger 
        logger = get_logger("update_searchables", config)
        enable_searchables_updates = config.auxillary.enable_searchables_updates

        # Exit if search is disabled
        if not enable_searchables_updates:
            logger.warning("Searchable updates are disabled in the configuration file, exiting.")
            return

        # Connect to the database
        conn = connect(
            host=config.db.db_host,
            port=config.db.db_port,
            database=config.db.db_database.value,
            user=config.db.db_username.value,
            password=config.db.db_password.value
        )
        logger.info("Connected to the database.")
        
        # Get IDs of tags & objects, which should be updated
        logger.info(f"Starting update in {mode} mode.")
        tag_ids, object_ids = get_ids(conn, mode)

        # Update searchables
        logger.info(f"Updating searchables for {len(tag_ids)} tags and {len(object_ids)} objects...")
        update_searchables(conn, tag_ids, object_ids)
        logger.info("Finished updating searchables.")
    except Exception as e:
        logger.error(e, exc_info=True)
        raise
    finally:
        # Close connection, if it was opened
        if enable_searchables_updates:
            if not conn.closed: 
                conn.close()
                logger.info("Disonnected from the database.")


if __name__ == "__main__":
    args = parse_args()
    main(args.mode)
