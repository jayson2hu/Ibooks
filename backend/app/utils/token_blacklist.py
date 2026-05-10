"""
JWT token blacklist helpers backed by Redis.
"""
import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import settings


def blacklist_key(token: str) -> str:
    """Return the Redis key for a blacklisted token."""
    return f"blacklist:{token}"


async def blacklist_token(token: str, ttl_seconds: int) -> None:
    """Store a token in the blacklist for its remaining lifetime."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await client.setex(blacklist_key(token), max(ttl_seconds, 1), "1")
    finally:
        await client.aclose()


async def is_token_blacklisted(token: str) -> bool:
    """Return whether a token has been invalidated."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        return await client.get(blacklist_key(token)) is not None
    except (RedisError, OSError):
        return False
    finally:
        await client.aclose()
