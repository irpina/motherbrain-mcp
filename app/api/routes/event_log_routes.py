"""Event Log API Routes — Read-only access to the unified activity log.

This endpoint provides the dashboard with access to the Kafka-style event log
that records all MCP tool calls, heartbeats, and system events.
"""

import asyncio
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.services.event_log import get_events
from app.queue.redis_queue import redis_async

router = APIRouter(tags=["event-log"])


@router.get("/api/event-log")
async def list_events(
    limit: int = Query(50, ge=1, le=500),
    since_id: int = Query(0, ge=0),
    topic: str = Query(""),
    service_id: str = Query("")
):
    """Get events from the unified activity log.
    
    Args:
        limit: Maximum number of events to return (default 50, max 500)
        since_id: Only return events with id > since_id (for polling)
        topic: Filter by topic ("chat", "proxy", "heartbeat", "system")
        service_id: Filter by service ID
        
    Returns:
        {
            "count": number of events returned,
            "filters": { "topic": ..., "service_id": ... },
            "events": [...]  # newest first
        }
    """
    events = await get_events(
        limit=limit,
        since_id=since_id,
        topic=topic,
        service_id=service_id
    )
    return {
        "count": len(events),
        "filters": {
            "topic": topic or None,
            "service_id": service_id or None
        },
        "events": events
    }


@router.get("/api/event-log/stream")
async def stream_events(
    topic: str = Query(""),
    service_id: str = Query("")
):
    """SSE stream of live event log entries.

    Clients connect once and receive newline-delimited SSE frames as events
    are appended. Optional topic/service_id filters are applied server-side.
    Sends a keepalive comment every 15 seconds so proxies don't close the
    connection.
    """
    async def _generator():
        pubsub = redis_async.pubsub()
        await pubsub.subscribe("event_log")
        try:
            while True:
                # Use wait_for so we can inject keepalives
                try:
                    msg = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue

                if msg is None:
                    await asyncio.sleep(0.05)
                    continue

                try:
                    event = json.loads(msg["data"])
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

                if topic and event.get("topic") != topic:
                    continue
                if service_id and event.get("service_id") != service_id:
                    continue

                yield f"data: {json.dumps(event)}\n\n"
        finally:
            await pubsub.unsubscribe("event_log")
            await pubsub.aclose()

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
