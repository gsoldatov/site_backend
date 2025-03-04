from aiohttp import web
from aiopg.sa.connection import SAConnection, Transaction
from datetime import datetime

from typing import TypeVar, overload, Any, Union, Awaitable, Callable, Protocol, Literal


request_time_key = web.AppKey("request_time_key", datetime)
request_id_key = web.AppKey("request_id_key", str)
request_monotonic_time_key = web.AppKey("request_monotonic_time_key", float)


class _LogEvent(Protocol):
    """ `log_event` function signature definition. """
    def __call__(self,
        str_level: str,
        event_type: str,
        message: str,
        details: dict[str, Any] | str = "",
        exc_info: bool | None = None
    ) -> None: ...
request_log_event_key = web.AppKey("request_log_event_key", _LogEvent)


class AuthCaches:
    """
    Provides caches objects' and tags' auth checks, which require running a DB query.
    """
    def __init__(self) -> None:
        self.modifiable_object_ids: set[int] = set()
        """ Set with object IDs, which are authorized for modification during the request. """
        self.applicable_tag_ids: set[int] = set()
        """ Set with tag IDs, which are authorized for being applied to or removed from objects during the request. """
request_auth_caches_key = web.AppKey("request_auth_cache_key", AuthCaches)


class UserInfo:
    """
    Dataclass for storing user information which corresponds to the provided `token`.
    """
    __slots__ = ["access_token", "is_anonymous", "user_id", "user_level", 
        "can_edit_objects", "access_token_expiration_time"]

    def __init__(
            self,
            access_token: str | None = None,
            user_id: int | None = None,
            user_level: Literal["admin", "user"] | None = None,
            can_edit_objects: bool | None = None,
            access_token_expiration_time: datetime | None = None
        ):
        self.access_token = access_token
        self.is_anonymous: bool = access_token is None
        
        self.user_id = user_id
        self.user_level = user_level
        self.can_edit_objects = can_edit_objects
        self.access_token_expiration_time = access_token_expiration_time

request_user_info_key = web.AppKey("request_user_info_key", UserInfo)

request_connection_key = web.AppKey("request_connection_key", SAConnection)
request_searchables_connection_key = web.AppKey("request_searchables_connection_key", SAConnection)
request_transaction_key = web.AppKey("request_transaction_key", Transaction) 


_T = TypeVar("_T")
_U = TypeVar("_U")


class Request(web.Request):
    """
    Subclass of web.Request with an app-like support for typing via web.AppKey keys.
    """
    @overload  # type: ignore[override]
    def __getitem__(self, key: web.AppKey[_T]) -> _T: ...

    @overload
    def __getitem__(self, key: str) -> Any: ...

    def __getitem__(self, key: Union[str, web.AppKey[_T]]) -> Any:
        return self._state[key] # type: ignore[index]

    @overload  # type: ignore[override]
    def __setitem__(self, key: web.AppKey[_T], value: _T) -> None: ...

    @overload
    def __setitem__(self, key: str, value: Any) -> None: ...

    def __setitem__(self, key: Union[str, web.AppKey[_T]], value: Any) -> None:
        self._state[key] = value    # type: ignore[index]
    
    @overload  # type: ignore[override]
    def get(self, key: web.AppKey[_T], default: None = ...) ->_T | None: ...

    @overload
    def get(self, key: web.AppKey[_T], default: _U) -> Union[_T, _U]: ...

    @overload
    def get(self, key: str, default: Any = ...) -> Any: ...

    def get(self, key: Union[str, web.AppKey[_T]], default: Any = None) -> Any:
        return self._state.get(key, default)    # type: ignore[arg-type]


Handler = Callable[[web.Request], Awaitable[web.Response]]
