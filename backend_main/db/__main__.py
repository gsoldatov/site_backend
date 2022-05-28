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
    
    from backend_main.db.logger import get_logger


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
    parser.set_defaults(force=False, revision=False, migrate=False)
    args = parser.parse_args()

    if args.revision and (args.message is None):
        parser.error("--revision argument must be specified with --message.")
    
    return args


def main():
    # Parse args
    args = parse_args()

    # Get config and logger
    config = get_config()
    logger = get_logger("main", config)
    logger.error(f"DB utility is starting with args {str(args)}...")

    # Revision
    if args.revision:
        logger.info(f"Starting database revision...")
        revision(config, args.message)
    
    # Migrations only
    elif args.migrate:
        logger.info(f"Starting database migration...")
        migrate_as_superuser(config)
        migrate(config)
    
    # Create user and database, then apply migrations
    else:
        cursor = None
        try:
            logger.info(f"Starting database initialization...")

            # Get app config and connect to the default database
            cursor = connect(host=config["db"]["db_host"], port=config["db"]["db_port"], database=config["db"]["db_init_database"].value,
                                user=config["db"]["db_init_username"].value, password=config["db"]["db_init_password"].value)
            logger.info(f"Connected to the default database.")
            
            # Drop existing user and database
            drop_user_and_db(config, cursor, args.force)

            # Create user and database
            create_user(config, cursor)
            create_db(config, cursor)
            
            # Apply migrations
            migrate_as_superuser(config)
            migrate(config)

            logger.info(f"Database initialization finished.")
        
        except InitDBException as e:
            logger.warning(e)
            logger.warning("Database initialization aborted.")
        
        except Exception as e:
            logger.error(e, exc_info=True)
            raise
        
        finally:
            if type(cursor) == CursorClass:
                disconnect(cursor)
                logger.info(f"Disconnected from the default database.")
    
    logger.info(f"DB utility finished running.")


if __name__ == "__main__":
    main()
