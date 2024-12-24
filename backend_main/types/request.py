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
        details: str = "",
        exc_info: bool | None = None
    ) -> None: ...
request_log_event_key = web.AppKey("request_log_event_key", _LogEvent)


class UserInfo:
    """
    Dataclass for storing user information which corresponds to the provided `token`.
    """
    __slots__ = ["access_token", "is_anonymous", "user_id", "user_level", 
        "can_edit_objects", "access_token_expiration_time"]

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token
        self.is_anonymous: bool = access_token is None
        
        self.user_id: int | None = None
        self.user_level: Literal["admin", "user"] | None = None
        self.can_edit_objects: bool | None = None
        self.access_token_expiration_time: datetime | None = None

request_user_info_key = web.AppKey("request_user_info_key", UserInfo)


class LoginRateLimitInfo:
    """
    Dataclass for storing login rate limiting information for the request sender.
    """
    __slots__ = ["ip_address", "failed_login_attempts", "cant_login_until"]

    def __init__(
            self,
            ip_address: str,
            failed_login_attempts: int,
            cant_login_until: datetime
        ):
        self.ip_address = ip_address
        self.failed_login_attempts = failed_login_attempts
        self.cant_login_until = cant_login_until


request_login_rate_limits_info_key = web.AppKey("request_login_rate_limits_info_key", LoginRateLimitInfo)


request_connection_key = web.AppKey("request_connection_key", SAConnection)
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
