async def close_connection_pools(app):
    if "engine" in app:
        app["engine"].close()
        await app["engine"].wait_closed()
        app.log_event("INFO", "app_cleanup", "Closed main connection pool.")

    # NOTE: Threaded connection pool is no longer used
    # if "threaded_pool" in app:
    #     app["threaded_pool"].closeall()
    #     app.log_event("INFO", "app_cleanup", "Closed threaded connection pool.")
    
    return app
