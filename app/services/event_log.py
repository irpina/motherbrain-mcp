"""Event Log Service — Database-backed Kafka-style append-only log.

This module provides persistent event logging for all tool calls
proxied through Motherbrain. Events are stored in PostgreSQL for
durability across restarts.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.event_log import EventLog


async def append_event(
    topic: str,
    service_id: str,
    tool_name: str,
    arguments: dict,
    response: Any,
    status: str,
    duration_ms: int,
    agent_id: Optional[str] = None,
) -> EventLog:
    """Append a new event to the log.
    
    Args:
        topic: Event category ("chat", "proxy", "heartbeat", "job", "system")
        service_id: The MCP service that was called (or "motherbrain" for internal)
        tool_name: The tool that was invoked
        arguments: The arguments passed to the tool
        response: The raw response from the service
        status: "ok" or "error"
        duration_ms: How long the call took
        agent_id: Optional ID of the agent that initiated the call
        
    Returns:
        The created event log entry
    """
    async with AsyncSessionLocal() as db:
        event = EventLog(
            topic=topic,
            service_id=service_id or None,
            agent_id=agent_id,
            tool_name=tool_name,
            arguments=arguments,
            response=response,
            status=status,
            duration_ms=duration_ms
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event


async def get_events(
    limit: int = 20,
    since_id: int = 0,
    topic: str = "",
    service_id: str = ""
) -> list[dict]:
    """Get events from the log with optional filtering.
    
    Args:
        limit: Maximum number of events to return
        since_id: Only return events with id > since_id (for polling)
        topic: Filter by topic ("chat", "proxy", "heartbeat", "job", "system")
        service_id: Filter by service ID
        
    Returns:
        List of events as dicts, newest first
    """
    async with AsyncSessionLocal() as db:
        query = select(EventLog)
        
        # Apply since_id filter (for polling)
        if since_id > 0:
            query = query.where(EventLog.id > since_id)
        
        if topic:
            query = query.where(EventLog.topic == topic)
        
        if service_id:
            query = query.where(EventLog.service_id == service_id)
        
        # Order by id descending (newest first), then limit
        query = query.order_by(desc(EventLog.id)).limit(limit)
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        return [_event_to_dict(e) for e in events]


async def get_latest_id() -> int:
    """Get the ID of the most recent event (for polling)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(EventLog.id)
            .order_by(desc(EventLog.id))
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        return latest if latest else 0


async def clear_events() -> None:
    """Clear all events (for testing)."""
    async with AsyncSessionLocal() as db:
        await db.execute(delete(EventLog))
        await db.commit()


def _event_to_dict(event: EventLog) -> dict:
    """Convert an EventLog ORM model to a dictionary.
    
    Maintains backward compatibility with the previous dataclass format.
    """
    return {
        "id": event.id,
        "timestamp": event.created_at.isoformat() if event.created_at else None,
        "topic": event.topic,
        "service_id": event.service_id,
        "agent_id": event.agent_id,
        "tool_name": event.tool_name,
        "arguments": event.arguments,
        "response": event.response,
        "status": event.status,
        "duration_ms": event.duration_ms
    }
