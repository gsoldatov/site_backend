import asyncio

from aiohttp import web

from backend_main.types import app_config_key


async def close_connection_pools(app: web.Application):
    # Disable request processing
    app["can_process_requests"]["value"] = False

    # Wait for searchable update tasks to complete
    if app[app_config_key].auxillary.enable_searchables_updates:
        while len(app["pending_tasks"]) > 0:
            await asyncio.sleep(0.1)
    
    # Close connection pool
    if "engine" in app:
        app["engine"].close()
        await app["engine"].wait_closed()
        app["log_event"]("INFO", "app_cleanup", "Closed main connection pool.")

    # NOTE: Threaded connection pool is no longer used
    # if "threaded_pool" in app:
    #     app["threaded_pool"].closeall()
    #     app["log_event"]("INFO", "app_cleanup", "Closed threaded connection pool.")
    
    return app
