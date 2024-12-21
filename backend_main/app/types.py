from aiohttp import web
from aiopg.sa.engine import Engine
from asyncio import Task
from logging import Logger
from typing import Protocol, TypedDict

from backend_main.app.config import Config


"""
NOTE on app typing:
The following typing options don't work for web.Application as of Python 3.10 & aiohttp 3.11:
1) using both `web.Application` & `TypedDict` as base classes for app (due to having different meta classes);
2) subclassing `web.Application` only & passing data via custom props instead of dict
   (`request.app` may link to a subapp, which does not have these props set up)

Possible options for typing are:
1) using `web.AppKey` objects for setting & accessing app storage items;
2) using only `TypedDict` or `web.Application` as the type of the app & casting to the other type whenever needed.

The first option is not supported by request storage by default, however the second will fail to propagate
types from app storage accessed via `request.config_dict`.
"""
app_config_key = web.AppKey("app_config_key", Config)

app_event_logger_key = web.AppKey("app_event_logger_key", Logger)
app_access_logger_key = web.AppKey("app_access_logger_key", Logger)

class _LogAccess(Protocol):
    """ `log_access` function signature definition. """
    def __call__(self,
        request_id: str,
        path: str,
        method: str,
        status: int,
        elapsed_time: float,
        user_id: int | str,
        remote: str | None,
        user_agent: str,
        referer: str
    ) -> None: ...
app_log_access_key = web.AppKey("app_log_access_key", _LogAccess)

class _LogEvent(Protocol):
    """ `log_event` function signature definition. """
    def __call__(self,
        level: str,
        event_type: str,
        message: str,
        details: str = "",
        exc_info: bool | None = None
    ) -> None: ...
app_log_event_key = web.AppKey("app_log_event_key", _LogEvent)

app_engine_key = web.AppKey("app_engine_key", Engine)
# tables: Any

app_pending_tasks_key = web.AppKey("app_pending_tasks_key", set[Task])

# NOTE: dict is used to avoid warnings about state change of a frozen app
_CanProcessRequests = TypedDict("_CanProcessRequests", {"value": bool})

app_can_process_requests_key = web.AppKey("app_can_process_requests_key", _CanProcessRequests)
