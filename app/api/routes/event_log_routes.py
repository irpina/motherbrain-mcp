"""Event Log API Routes — Read-only access to the unified activity log.

This endpoint provides the dashboard with access to the Kafka-style event log
that records all MCP tool calls, heartbeats, and system events.
"""

from fastapi import APIRouter, Query
from app.services.event_log import get_events

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
