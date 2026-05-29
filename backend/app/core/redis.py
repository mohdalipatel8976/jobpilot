"""
JobPilot — Redis Client
Async Redis connection with helper methods for caching.
"""

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

# Global Redis client — initialized during app startup
redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> aioredis.Redis:
    """Initialize the async Redis connection pool."""
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    # Test connection
    await redis_client.ping()
    return redis_client


async def close_redis():
    """Close the Redis connection pool."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def get_redis() -> aioredis.Redis:
    """Get the Redis client instance."""
    if redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    return redis_client


# -------------------------------------------------------
# Cache Helper Methods
# -------------------------------------------------------

async def cache_get(key: str) -> Optional[Any]:
    """Get a value from Redis cache, deserializing JSON."""
    client = get_redis()
    value = await client.get(key)
    if value is not None:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set a value in Redis cache with TTL (default 5 minutes)."""
    client = get_redis()
    serialized = json.dumps(value, default=str)
    await client.set(key, serialized, ex=ttl)


async def cache_delete(key: str) -> None:
    """Delete a key from Redis cache."""
    client = get_redis()
    await client.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern."""
    client = get_redis()
    async for key in client.scan_iter(match=pattern):
        await client.delete(key)
