"""
Redis-backed fixed-window rate limiting utilities.
"""
import redis.asyncio as redis

from app.config import settings


async def check_rate_limit(key: str, max_calls: int, window_seconds: int) -> bool:
    """
    Return True when the request is allowed.

    Backend failures propagate to the caller so security-sensitive endpoints can
    fail closed instead of silently disabling brute-force protection.
    """
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window_seconds)
        return count <= max_calls
    finally:
        await client.aclose()
