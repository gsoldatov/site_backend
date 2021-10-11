"""
Database operations related to login_rate_limits table.
"""
from datetime import datetime, timedelta
from math import ceil

from aiohttp import web
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert


async def add_login_rate_limit_to_request(request):
    """
    Gets login rate limit information for the request sender and adds it to request.
    If `cant_login_until` exceeds current time, raises 403.
    """
    login_rate_limits = request.config_dict["tables"]["login_rate_limits"]

    result = await request["conn"].execute(
        select([login_rate_limits.c.failed_login_attempts, login_rate_limits.c.cant_login_until])
        .where(login_rate_limits.c.ip_address == request.remote)
    )
    row = await result.fetchone()
    request.login_rate_limit_info = LoginRateLimitInfo(request.remote, row[0], row[1]) if row is not None else LoginRateLimitInfo(request.remote)

    seconds_until_logging_in_is_available = ceil((request.login_rate_limit_info.cant_login_until - datetime.utcnow()).total_seconds())
    if seconds_until_logging_in_is_available > 0:
        raise web.HTTPTooManyRequests(headers={"Retry-After": str(seconds_until_logging_in_is_available)})


async def upsert_login_rate_limit(request, login_rate_limit_info):
    """
    Upserts provided `login_rate_limit_info` into the database.
    """
    login_rate_limits = request.config_dict["tables"]["login_rate_limits"]
    data = {attr: getattr(login_rate_limit_info, attr) for attr in ("ip_address", "failed_login_attempts", "cant_login_until")}

    await request["conn"].execute(
        insert(login_rate_limits)
        .values(data)
        .on_conflict_do_update(
            index_elements=[login_rate_limits.c.ip_address],
            set_=data
        )
    )


async def delete_login_rate_limits(request, ip_addresses):
    """
    Deletes login rate limits for the specified `ip_addresses`.
    """
    login_rate_limits = request.config_dict["tables"]["login_rate_limits"]

    result = await request["conn"].execute(
        login_rate_limits.delete()
        .where(login_rate_limits.c.ip_address.in_(ip_addresses))
        .returning(login_rate_limits.c.ip_address)
    )

    return ip_addresses


class LoginRateLimitInfo:
    """
    Dataclass for storing login rate limiting information for the request sender.
    """
    __slots__ = ["ip_address", "failed_login_attempts", "cant_login_until"]

    def __init__(self, ip_address, failed_login_attempts = None, cant_login_until = None):
        self.ip_address = ip_address
        self.failed_login_attempts = failed_login_attempts if failed_login_attempts is not None else 0
        self.cant_login_until = cant_login_until if cant_login_until is not None else datetime.utcnow() + timedelta(minutes=-1)
