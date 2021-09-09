"""
Database initialization + migration utility.
"""
import argparse
from psycopg2.extensions import cursor as CursorClass

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(sys.path[0])))

    from backend_main.config import get_config
    from backend_main.db.init_db import InitDBException, connect, disconnect, \
        drop_user_and_db, create_user, create_db, revision, migrate_as_superuser, migrate


def parse_args():
    # Parse CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", help="Delete the database speicified in the config file, if it exists.",
                        action="store_true")
    parser.add_argument("--revision", help="Run Alembic revision command only.",
                        action="store_true")
    parser.add_argument("--message", help="Message to add to the revision.")
    parser.add_argument("--migrate", help="Apply migrations to the database only.",
                        action="store_true")
    parser.set_defaults(force=False, revision=False, message="", migrate=False)
    return parser.parse_args()


def main():
    args = parse_args()

    # Revision
    if args.revision:
        revision(message=args.message)
    
    # Migrations only
    elif args.migrate:
        db_config  = get_config()["db"]
        migrate_as_superuser(db_config)
        migrate()
    
    # Create user and database, then apply migrations
    else:
        cursor = None
        try:
            # Get app config and connect to the default database
            db_config = get_config()["db"]
            cursor = connect(host=db_config["db_host"], port=db_config["db_port"], database=db_config["db_init_database"],
                                user=db_config["db_init_username"], password=db_config["db_init_password"])
            
            # Drop existing user and database
            drop_user_and_db(cursor, db_config, args.force)

            # Create user and database
            if db_config["create_user_required"]:
                create_user(cursor=cursor, user=db_config["db_username"], password=db_config["db_password"])
            create_db(cursor=cursor, db_name=db_config["db_database"], db_owner=db_config["db_username"])
            
            # Apply migrations
            migrate_as_superuser(db_config)
            migrate()
        except InitDBException as e:
            print(e)
            print("Database initialization aborted.")
        finally:
            if type(cursor) == CursorClass:
                disconnect(cursor)


if __name__ == "__main__":
    main()
