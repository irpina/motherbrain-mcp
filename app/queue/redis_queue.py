import json
from typing import Optional
import redis.asyncio as redis
from app.core.config import settings


client = redis.from_url(settings.REDIS_URL)


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
