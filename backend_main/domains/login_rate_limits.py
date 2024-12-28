from aiohttp import web
from datetime import timedelta
from math import ceil

from backend_main.db_operations2.login_rate_limits import \
    get_login_rate_limit as _get_login_rate_limit, \
    upsert_login_rate_limit as _upsert_login_rate_limit, \
    delete_login_rate_limits as _delete_login_rate_limits

from backend_main.types.domains.login_rate_limits import LoginRateLimit
from backend_main.types.request import Request, request_time_key, request_log_event_key


async def get_request_sender_login_rate_limit(request: Request) -> LoginRateLimit:
    """
    Gets current login rate limit for the `request` sender.
    If a limit is present, raises HTTP 429 exception.
    Otherwise, returns current logim rate limit.
    """
    limit = await _get_login_rate_limit(request, get_request_sender(request))
    seconds_until_logging_in_is_available = ceil((limit.cant_login_until - request[request_time_key]).total_seconds())
    if seconds_until_logging_in_is_available > 0:
        request[request_log_event_key]("WARNING", "domain", "Login rate limit is exceeded.")
        raise web.HTTPTooManyRequests(headers={"Retry-After": str(seconds_until_logging_in_is_available)})
    return limit


async def increase_request_sender_login_rate_limit(
        request: Request,
        current_limit: LoginRateLimit
    ) -> None:
    """ Increases `current_limit` of the `request` sender. """
    cant_login_until = request[request_time_key] + \
        timedelta(seconds=get_login_attempts_timeout_in_seconds(current_limit.failed_login_attempts))

    new_limits = LoginRateLimit(
        ip_address=current_limit.ip_address,
        failed_login_attempts=current_limit.failed_login_attempts + 1,
        cant_login_until=cant_login_until
    )
    
    await _upsert_login_rate_limit(request, new_limits)


async def delete_request_sender_login_rate_limit(request: Request) -> None:
    await _delete_login_rate_limits(request, [get_request_sender(request)])


def get_login_attempts_timeout_in_seconds(failed_login_attempts: int) -> int:
    """
    Returns the number of seconds before the next possible login attempt for the provided `failed_login_attempts` number.
    Number of seconds is negative for the first attempts.
    """
    _LOGIN_TIMEOUTS = [-60] * 9
    _LOGIN_TIMEOUTS.extend([5, 10, 20, 30, 60, 120, 600, 1200, 1800])
    _LOGIN_TIMEOUT_DEFAULT = 3600

    return _LOGIN_TIMEOUTS[failed_login_attempts] if failed_login_attempts < len(_LOGIN_TIMEOUTS) else _LOGIN_TIMEOUT_DEFAULT


def get_request_sender(request: Request) -> str:
    """ Type guard for request.remote, which can be None. """
    return request.remote or "Unknown"
