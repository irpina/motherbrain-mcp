# Queue — Redis Operations

## Purpose
Abstraction layer for Redis operations used by the job queue and pub/sub.

## Structure

```
queue/
└── redis_queue.py    # All Redis interactions
```

## Key Functions

```python
# Job Queue (Redis List)
async def enqueue_job(job_id: str) -> None
async def dequeue_job() -> Optional[str]

# Pub/Sub (Redis PubSub)
async def publish_event(channel: str, data: dict) -> None
async def subscribe(channel: str) -> AsyncIterator[str]

# Logs (Redis String/JSON)
async def append_log(job_id: str, log: str) -> None
async def get_logs(job_id: str) -> list[str]
```

## Redis Patterns

### Job Queue Pattern

Uses Redis Lists for FIFO queue:
- `RPUSH job_queue <job_id>` — add to end
- `LPOP job_queue` — take from front (blocking)

### Pub/Sub Pattern

Uses Redis PubSub for real-time events:
- `PUBLISH channel data` — broadcast
- `SUBSCRIBE channel` — listen

## Adding New Queue Operations

Add functions to `redis_queue.py`:

```python
async def my_new_operation(key: str, value: str) -> None:
    """Description of what this does.
    
    Args:
        key: Redis key
        value: Value to store
    """
    await client.set(key, value)
```

## Extension Points

**Future enhancements** (marked with `# FUTURE:`):
- Priority queues (multiple Redis lists)
- Delayed jobs (Redis sorted sets with timestamps)
- Topic-based routing (channel patterns)

## Testing

Redis operations can be mocked for tests:

```python
@pytest.mark.asyncio
async def test_enqueue_job():
    with patch('app.queue.redis_queue.client') as mock_client:
        await enqueue_job("job-123")
        mock_client.rpush.assert_called_with("job_queue", "job-123")
```
