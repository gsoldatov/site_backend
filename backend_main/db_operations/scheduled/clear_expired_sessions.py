"""
Clears expired records from `sessions` table.
"""
from datetime import datetime

from psycopg2.extensions import cursor as CursorClass

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(sys.path[0]))))

from backend_main.config import get_config
from backend_main.db.init_db import connect, disconnect
    

def main(config = None):
    cursor = None
    try:
        # Get app config and connect to the database
        db_config = (config or get_config())["db"]
        cursor = connect(host=db_config["db_host"], port=db_config["db_port"], database=db_config["db_database"].value,
                            user=db_config["db_username"].value, password=db_config["db_password"].value)
        
        # Delete sessions, which are expired or belong to users who can't login
        current_time = datetime.utcnow()
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
    finally:
        if type(cursor) == CursorClass:
            disconnect(cursor)


if __name__ == "__main__":
    main()
