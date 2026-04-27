from __future__ import annotations

from typing import Optional

import redis.asyncio as aioredis

from config_reader import config


def _redis_url() -> Optional[str]:
    host = config.redis_host
    port = config.redis_port
    db = config.redis_db
    if not host or not port:
        return None
    return (
        f'redis://{host.get_secret_value()}:'
        f'{port.get_secret_value()}/'
        f'{db.get_secret_value() if db else "0"}'
    )


async def connect_redis():
    url = _redis_url()
    if not url:
        return None
    return aioredis.from_url(url, decode_responses=True)


async def incr_with_ttl(
    client,
    key: str,
    ttl_seconds: int,
) -> int:
    n = int(await client.incr(key))
    if n == 1:
        await client.expire(key, ttl_seconds)
    return n


async def assert_under_limit(
    client,
    key: str,
    max_value: int,
    ttl_seconds: int = 3600,
) -> None:
    if client is None:
        return
    n = await incr_with_ttl(client, key, ttl_seconds)
    if n > max_value:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=429,
            detail='Слишком много попыток. Попробуйте позже.',
        )
