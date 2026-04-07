"""Heartbeat API Routes — Agent check-in and trigger delivery.

Agents poll this endpoint to:
1. Mark themselves as online
2. Receive any pending triggers (mentions, jobs, etc.)

This enables push-like delivery without websockets — agents heartbeat
every few seconds and receive queued triggers in the response.
"""

from fastapi import APIRouter
from datetime import datetime, timezone
from typing import Any

from app.services.agent_registry import (
    register_heartbeat,
    get_pending_triggers,
)
from app.services.event_log import append_event

router = APIRouter(tags=["heartbeat"])


@router.post("/api/heartbeat/{agent_name}")
async def heartbeat(agent_name: str) -> dict[str, Any]:
    """Agent checks in. Returns any pending triggers.
    
    This is the heartbeat endpoint agents call periodically to:
    - Mark themselves as online
    - Receive any triggers (mentions, jobs) queued for them
    
    Args:
        agent_name: The unique name of the agent (e.g., "tester", "claude")
        
    Returns:
        {
            "status": "ok",
            "timestamp": "2024-01-15T10:30:00Z",
            "agent_name": "tester",
            "triggers": [
                {
                    "job_id": "uuid",
                    "channel": "motherbrain",
                    "sender": "user",
                    "text": "@tester hello there",
                    "addressed_to": "tester"
                }
            ]
        }
        
    Example:
        POST /api/heartbeat/tester
        → {"status": "ok", "triggers": [], ...}
        
        # After user sends @tester hello:
        POST /api/heartbeat/tester
        → {"status": "ok", "triggers": [{"job_id": "...", "text": "@tester hello", ...}]}
    """
    # Record this heartbeat
    register_heartbeat(agent_name)
    
    # Get any pending triggers for this agent
    triggers = get_pending_triggers(agent_name)
    
    # Log the heartbeat event
    append_event(
        topic="heartbeat",
        service_id="motherbrain",
        tool_name="heartbeat",
        arguments={"agent_name": agent_name},
        response={"triggers_delivered": len(triggers)},
        status="ok",
        duration_ms=0
    )
    
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": agent_name,
        "triggers": triggers,
    }
