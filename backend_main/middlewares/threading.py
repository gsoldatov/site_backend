"""
    Middleware for dispatching task execution in separate threads.
    Currently runs searchable data updates whenever original data was modified.
"""
from aiohttp import web
from threading import Thread

from backend_main.db_operations.searchables import searchables_update_manager


@web.middleware
async def threading_middleware(request, handler):
    result = await handler(request)

    # Skip middleware for CORS requests
    if request.method not in ("OPTIONS", "HEAD"):
        dispatch_searchables_update(request)

    return result


def dispatch_searchables_update(request):
    """
    Starts update of `searchables` table if its updates are enabled and searchable data was modified during request.
    """
    def _task(request):
        app = request.app
        conn = app["threaded_pool"].getconn()

        try:
            tag_ids = tuple((_ for _ in request.get("searchable_updates_tag_ids", set())))
            object_ids = tuple((_ for _ in request.get("searchable_updates_object_ids", set())))
            searchables_update_manager(conn, tag_ids, object_ids)
        finally:
            app["threaded_pool"].putconn(conn)

    if request.config_dict["config"]["auxillary"]["enable_searchables_updates"] \
        and ("searchable_updates_tag_ids" in request or "searchable_updates_object_ids" in request):
        Thread(target=_task, args=(request,)).start()
