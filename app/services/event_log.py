"""Event Log Service — Kafka-style append-only log for MCP tool calls.

This module provides an in-memory event log that records every tool call
proxied through Motherbrain. The LLM polls get_event_log() to read results
and decide next actions.
"""

from datetime import datetime, timezone
from typing import Any
from dataclasses import dataclass, asdict


@dataclass
class MCPEvent:
    """A single MCP tool call event."""
    id: int
    timestamp: str
    topic: str  # "chat", "proxy", "heartbeat", "job", "system", etc.
    service_id: str
    tool_name: str
    arguments: dict
    response: Any
    status: str  # "ok" | "error"
    duration_ms: int


# In-memory event store
_events: list[MCPEvent] = []
_next_id: int = 1


def append_event(
    topic: str,
    service_id: str,
    tool_name: str,
    arguments: dict,
    response: Any,
    status: str,
    duration_ms: int
) -> MCPEvent:
    """Append a new event to the log.
    
    Args:
        topic: Event category ("chat", "proxy", "heartbeat", "job", "system")
        service_id: The MCP service that was called (or "motherbrain" for internal)
        tool_name: The tool that was invoked
        arguments: The arguments passed to the tool
        response: The raw response from the service
        status: "ok" or "error"
        duration_ms: How long the call took
        
    Returns:
        The created event
    """
    global _next_id
    
    event = MCPEvent(
        id=_next_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        topic=topic,
        service_id=service_id,
        tool_name=tool_name,
        arguments=arguments,
        response=response,
        status=status,
        duration_ms=duration_ms
    )
    
    _events.append(event)
    _next_id += 1
    
    # Keep only last 1000 events to prevent unbounded growth
    if len(_events) > 1000:
        _events.pop(0)
    
    return event


def get_events(
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
    # Filter events newer than since_id
    filtered = [e for e in _events if e.id > since_id]
    
    # Apply topic filter if specified
    if topic:
        filtered = [e for e in filtered if e.topic == topic]
    
    # Apply service_id filter if specified
    if service_id:
        filtered = [e for e in filtered if e.service_id == service_id]
    
    # Get last 'limit' events, reversed to be newest-first
    result = filtered[-limit:] if limit < len(filtered) else filtered
    
    return [asdict(e) for e in reversed(result)]


def get_latest_id() -> int:
    """Get the ID of the most recent event (for polling)."""
    return _events[-1].id if _events else 0


def clear_events():
    """Clear all events (for testing)."""
    global _events, _next_id
    _events = []
    _next_id = 1
