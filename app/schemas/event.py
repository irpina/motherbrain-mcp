"""Event Schemas — For generic event ingestion from MCP servers.

Any MCP server can POST events to Motherbrain. Events become jobs
that the LLM can see and act upon.
"""

from typing import Optional
from pydantic import BaseModel


class EventCreate(BaseModel):
    """Schema for ingesting events from MCP servers.
    
    This is the contract any MCP server uses to notify Motherbrain
    that something happened. The event becomes a pending job that	he LLM can discover and act upon.
    
    Example:
        {
            "service_id": "agentchattr-mcp",
            "event_type": "message_received",
            "payload": {
                "channel": "general",
                "sender": "user",
                "text": "@claude do something"
            },
            "topic": "general"
        }
    """
    service_id: str
    """The service_id of the MCP server sending the event.
    Must match a registered MCP service in Motherbrain."""
    
    event_type: str
    """What happened. Becomes the job.type.
    Examples: "message_received", "file_changed", "alert_triggered""
    """
    
    payload: dict
    """Arbitrary data about the event. Becomes the job.payload.
    The LLM uses this to understand what needs to be done."""
    
    topic: Optional[str] = None
    """Optional topic/channel for filtering. Becomes job.topic."""
