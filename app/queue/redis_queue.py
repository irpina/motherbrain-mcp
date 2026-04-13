import json
from typing import Optional
import redis.asyncio as redis
from app.core.config import settings


client = redis.from_url(settings.REDIS_URL)

# Export redis for direct access (pub/sub, etc.)
redis_async = client


async def enqueue_job(job_id: str):
    """Add a job ID to the queue."""
    await client.rpush("job_queue", job_id)


async def dequeue_job() -> Optional[str]:
    """Remove and return the next job ID from the queue."""
    result = await client.lpop("job_queue")
    return result.decode() if result else None


async def publish_event(channel: str, data: dict):
    """Publish an event to a Redis channel."""
    await client.publish(channel, json.dumps(data))


async def append_log(job_id: str, log: str):
    """Append a log entry to a job's log store."""
    log_key = f"job_logs:{job_id}"
    existing = await client.get(log_key)
    logs = json.loads(existing) if existing else []
    logs.append(log)
    await client.set(log_key, json.dumps(logs))


async def set_key(key: str, value: str, ttl: int = 3600):
    """Store a value in Redis with a TTL.
    
    Args:
        key: The Redis key
        value: The value to store
        ttl: Time to live in seconds (default: 1 hour)
    """
    await client.set(key, value, ex=ttl)


async def get_key(key: str) -> str | None:
    """Get a value from Redis.
    
    Args:
        key: The Redis key
    
    Returns:
        The value as a string, or None if not found or expired.
    """
    result = await client.get(key)
    return result.decode() if result else None


async def keys(pattern: str) -> list[bytes]:
    """Get all keys matching a pattern.
    
    Args:
        pattern: Redis key pattern (e.g., "chat_presence:general:*")
    
    Returns:
        List of matching keys as bytes.
    """
    return await client.keys(pattern)

async def delete_key(key: str):
    """Delete a key from Redis."""
    await client.delete(key)
