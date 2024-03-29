"""
    Middleware for dispatching additional async tasks.
    Runs searchable data updates whenever original data was modified.
"""
import asyncio

from aiohttp import web

from backend_main.db_operations.searchables import update_searchables_coro


@web.middleware
async def tasks_middleware(request, handler):
    result = await handler(request)

    # Skip middleware for CORS requests
    if request.method not in ("OPTIONS", "HEAD"):
        dispatch_searchables_update_coro(request)

    return result


def dispatch_searchables_update_coro(request):
    """
    Dispatches an async task to update searchable data, if seachable updates are enabled in the configuration
    and any searchable item was changed during a request.
    """
    # Exit if searchable update is disabled or no data was updated
    if not request.app["config"]["auxillary"]["enable_searchables_updates"]: return

    tag_ids = tuple((_ for _ in request.get("searchable_updates_tag_ids", set())))
    object_ids = tuple((_ for _ in request.get("searchable_updates_object_ids", set())))
    if not tag_ids and not object_ids: return

    # Set up a task to update searchables
    async def task_coro(request, tag_ids, object_ids):
        try:
            await update_searchables_coro(request, tag_ids, object_ids)
            request.log_event("INFO", "task_coro", "Updated searchables", details=f"object_ids = {object_ids}, tag_ids = {tag_ids}")
        except Exception as e:
            request.log_event("ERROR", "task_coro", "Error during searchables update", exc_info=True)

    task = asyncio.create_task(task_coro(request, tag_ids, object_ids))

    # Store a reference on the task during its execution 
    # to avoid it being destroyed by the garbage collector
    request.app["pending_tasks"].add(task)
    task.add_done_callback(request.app["pending_tasks"].discard)
