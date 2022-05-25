async def close_connection_pools(app):
    app["engine"].close()
    await app["engine"].wait_closed()

    if "threaded_pool" in app:
        app["threaded_pool"].closeall()
    
    return app

    # TODO log connection pools closing
