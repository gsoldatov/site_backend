"""
Clears records, which expired more than 12 hours ago from `login_rate_limits` table.
"""
from datetime import datetime, timedelta

from psycopg2.extensions import cursor as CursorClass

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(sys.path[0])))

from backend_main.config import get_config
from backend_main.db.init_db import connect, disconnect
    

def main(config = None):
    cursor = None
    try:
        # Get app config and connect to the database
        db_config = (config or get_config())["db"]
        cursor = connect(host=db_config["db_host"], port=db_config["db_port"], database=db_config["db_database"],
                            user=db_config["db_username"], password=db_config["db_password"])
        
        # Delete sessions with `expiration_time` < current_time - 12 hours
        threshold = datetime.utcnow() - timedelta(hours=12)
        cursor.execute(f"DELETE FROM login_rate_limits WHERE cant_login_until < '{threshold}'")
    finally:
        if type(cursor) == CursorClass:
            disconnect(cursor)


if __name__ == "__main__":
    main()
