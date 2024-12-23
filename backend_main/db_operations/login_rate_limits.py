"""
Database operations related to login_rate_limits table.
"""
from datetime import timedelta
from math import ceil

from aiohttp import web
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend_main.types.app import app_tables_key
from backend_main.types.request import LoginRateLimitInfo, request_time_key, request_connection_key, \
    request_login_rate_limits_info_key


async def add_login_rate_limit_to_request(request):
    """
    Gets login rate limit information for the request sender and adds it to request.
    If `cant_login_until` exceeds current time, raises 403.
    """
    login_rate_limits = request.config_dict[app_tables_key].login_rate_limits
    request_time = request[request_time_key]

    result = await request[request_connection_key].execute(
        select(login_rate_limits.c.failed_login_attempts, login_rate_limits.c.cant_login_until)
        .where(login_rate_limits.c.ip_address == request.remote)
    )
    row = await result.fetchone()
    ip_address = request.remote
    failed_login_attempts = row[0] if row is not None else 0
    cant_login_until = row[1] if row is not None else request_time + timedelta(minutes=-1)
    request[request_login_rate_limits_info_key] = LoginRateLimitInfo(ip_address, failed_login_attempts, cant_login_until)

    seconds_until_logging_in_is_available = ceil((cant_login_until - request_time).total_seconds())
    if seconds_until_logging_in_is_available > 0:
        raise web.HTTPTooManyRequests(headers={"Retry-After": str(seconds_until_logging_in_is_available)})


async def upsert_login_rate_limit(request, login_rate_limit_info):
    """
    Upserts provided `login_rate_limit_info` into the database.
    """
    login_rate_limits = request.config_dict[app_tables_key].login_rate_limits
    data = {attr: getattr(login_rate_limit_info, attr) for attr in ("ip_address", "failed_login_attempts", "cant_login_until")}

    await request[request_connection_key].execute(
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
    login_rate_limits = request.config_dict[app_tables_key].login_rate_limits

    result = await request[request_connection_key].execute(
        login_rate_limits.delete()
        .where(login_rate_limits.c.ip_address.in_(ip_addresses))
        .returning(login_rate_limits.c.ip_address)
    )

    return ip_addresses
