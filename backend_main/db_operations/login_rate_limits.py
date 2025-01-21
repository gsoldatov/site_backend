"""
Database operations related to login_rate_limits table.
"""
from datetime import timedelta

from aiohttp import web
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend_main.types.app import app_tables_key
from backend_main.types.domains.login_rate_limits import LoginRateLimit
from backend_main.types.request import Request, request_time_key, request_connection_key


async def get_login_rate_limit(request: Request, ip_address: str) -> LoginRateLimit:
    """
    Returns login rate limit information for the `ip_address`.
    """
    login_rate_limits = request.config_dict[app_tables_key].login_rate_limits

    result = await request[request_connection_key].execute(
        select(
            login_rate_limits.c.ip_address,
            login_rate_limits.c.failed_login_attempts,
            login_rate_limits.c.cant_login_until
        )
        .where(login_rate_limits.c.ip_address == ip_address)
    )

    row = await result.fetchone()
    return LoginRateLimit(**row) if row is not None else LoginRateLimit(
        ip_address=ip_address,
        failed_login_attempts=0,
        cant_login_until=request[request_time_key] + timedelta(minutes=-1)
    )


async def upsert_login_rate_limit(request: Request, login_rate_limit: LoginRateLimit) -> None:
    """
    Upserts provided `login_rate_limit` into the database.
    """
    login_rate_limits = request.config_dict[app_tables_key].login_rate_limits
    values = login_rate_limit.model_dump()

    await request[request_connection_key].execute(
        insert(login_rate_limits)
        .values(values)
        .on_conflict_do_update(
            index_elements=[login_rate_limits.c.ip_address],
            set_=values
        )
    )


async def delete_login_rate_limits(request: Request, ip_addresses: list[str]) -> None:
    """
    Deletes login rate limits for the specified `ip_addresses`.
    """
    login_rate_limits = request.config_dict[app_tables_key].login_rate_limits

    await request[request_connection_key].execute(
        login_rate_limits.delete()
        .where(login_rate_limits.c.ip_address.in_(ip_addresses))
    )
