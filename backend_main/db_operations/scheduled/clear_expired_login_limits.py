"""
Clears records, which expired more than 12 hours ago from `login_rate_limits` table.
"""
from datetime import datetime, timezone, timedelta

from psycopg2.extensions import cursor as CursorClass

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(sys.path[0]))))

from backend_main.config import get_config
from backend_main.db.init_db import connect, disconnect
from backend_main.logging.loggers.scheduled import get_logger
    

def main(config = None):
    try:
        # Get config and logger
        config = config or get_config()
        logger = get_logger("clear_expired_login_limits", config)

        # Connect to the database
        cursor = connect(host=config["db"]["db_host"], port=config["db"]["db_port"], database=config["db"]["db_database"].value,
                            user=config["db"]["db_username"].value, password=config["db"]["db_password"].value)
        logger.info("Connected to the database.")
        
        # Delete sessions with `expiration_time` < current_time - 12 hours
        threshold = datetime.now(tz=timezone.utc) - timedelta(hours=12)
        cursor.execute(f"DELETE FROM login_rate_limits WHERE cant_login_until < '{threshold}'")
        logger.info("Deleted expired login limits.")
    except Exception as e:
        logger.error(e, exc_info=True)
        raise
    finally:
        if type(cursor) == CursorClass:
            disconnect(cursor)
            logger.info("Disconnected from the database.")


if __name__ == "__main__":
    main()
