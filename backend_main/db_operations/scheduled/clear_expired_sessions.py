"""
Clears expired records from `sessions` table.
"""
from datetime import datetime, timezone

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
        logger = get_logger("clear_expired_sessions", config)

        # Connect to the database
        cursor = connect(
            host=config.db.db_host,
            port=config.db.db_port,
            database=config.db.db_database.value,
            user=config.db.db_username.value,
            password=config.db.db_password.value
        )
        logger.info("Connected to the database.")
        
        # Delete sessions, which are expired or belong to users who can't login
        current_time = datetime.now(tz=timezone.utc)
        cursor.execute(f"""
            DELETE FROM sessions
            WHERE access_token IN (
                SELECT sessions.access_token
                FROM sessions
                LEFT JOIN users
                ON users.user_id = sessions.user_id
                WHERE 
                    sessions.expiration_time < '{current_time}'
                    OR users.can_login = FALSE
            )
        """)
        logger.info("Deleted expired sessions.")
    except Exception as e:
        logger.error(e, exc_info=True)
        raise
    finally:
        if type(cursor) == CursorClass:
            disconnect(cursor)
            logger.info("Disconnected from the database.")


if __name__ == "__main__":
    main()
