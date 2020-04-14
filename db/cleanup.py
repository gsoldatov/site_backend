async def close_engine(app):
    app["engine"].close()
    await app["engine"].wait_closed()
    return app