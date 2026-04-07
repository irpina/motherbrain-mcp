"""Heartbeat API Routes — Agent check-in and trigger delivery.

Agents poll this endpoint to:
1. Mark themselves as online
2. Receive any pending triggers (mentions, jobs, etc.)

This enables push-like delivery without websockets — agents heartbeat
every few seconds and receive queued triggers in the response.
"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.agent_registry import (
    register_heartbeat,
    get_pending_triggers,
)
from app.services.agent_service import update_heartbeat as update_agent_heartbeat

router = APIRouter(tags=["heartbeat"])


@router.post("/api/heartbeat/{agent_name}")
async def heartbeat(
    agent_name: str,
    agent_id: str = Query(""),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Agent checks in. Returns any pending triggers.
    
    This is the heartbeat endpoint agents call periodically to:
    - Mark themselves as online
    - Receive any triggers (mentions, jobs) queued for them
    
    Args:
        agent_name: The unique name of the agent (e.g., "tester", "claude")
        agent_id: Optional DB agent ID to update last_heartbeat in database
        
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
        
        POST /api/heartbeat/tester?agent_id=abc-123
        → Updates DB last_heartbeat as well as in-memory registry
    """
    # Record this heartbeat in in-memory registry
    register_heartbeat(agent_name)
    
    # Also update DB last_heartbeat if agent_id provided
    if agent_id:
        await update_agent_heartbeat(db, agent_id)
    
    # Get any pending triggers for this agent
    triggers = get_pending_triggers(agent_name)

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": agent_name,
        "triggers": triggers,
    }
