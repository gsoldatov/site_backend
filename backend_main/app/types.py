from aiohttp import web

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

TODO
? test request subclass with web.AppKey support for request storage;

- use typed dict for app & cast it to web.Application whenever required
- replace access to app config via prop with dict access;
- replace request.app["... with request.config_dict["...;

- add comments of typing approach (multiple inheritance with TypedDict, subclassing with custom props (not working with subapps)),
    web.AppKey usage (requires implementation)
"""
app_config_key = web.AppKey("app_config_key", Config)
# event_logger: Any
# access_logger: Any

# engine: Any
# tables: Any
# pending_tasks: Any
# can_process_requests: Any