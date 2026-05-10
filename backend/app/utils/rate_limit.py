"""
Redis-backed fixed-window rate limiting utilities.
"""
import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import settings


async def check_rate_limit(key: str, max_calls: int, window_seconds: int) -> bool:
    """
    Return True when the request is allowed.

    Redis failures are treated as allow to avoid taking authentication offline when
    the cache is temporarily unavailable.
    """
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window_seconds)
        return count <= max_calls
    except (RedisError, OSError):
        return True
    finally:
        await client.aclose()
