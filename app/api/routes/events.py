"""Event API Routes — Generic event ingestion from MCP servers.

Any MCP server can POST events to this endpoint. Events enqueue triggers
for agent delivery via the heartbeat system. Jobs are explicitly created
by the LLM or user — not auto-generated from events.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_api_key
from app.db.session import get_db
from app.schemas.event import EventCreate
from app.services import mcp_service_service
from app.services.agent_registry import enqueue_trigger


router = APIRouter(tags=["events"])


@router.post("/events", status_code=status.HTTP_200_OK)
async def ingest_event(
    event: EventCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Ingest an event from an MCP server.
    
    Events enqueue triggers for heartbeat delivery. They do NOT create jobs.
    Jobs are explicitly created by LLMs or users via POST /jobs.
    
    Args:
        event: The event to ingest
        db: Database session
    
    Returns:
        {"status": "ok", "triggers_enqueued": N}
    
    Raises:
        HTTPException 400: If service_id not registered
    
    Example request:
        POST /events
        X-API-Key: supersecret
        {
            "service_id": "agentchattr-mcp",
            "event_type": "message_received",
            "payload": {
                "channel": "general",
                "sender": "user",
                "text": "@claude do something"
            },
            "topic": "general",
            "addressed_to": ["claude"]
        }
    
    Example response:
        {"status": "ok", "triggers_enqueued": 1}
    """
    # Verify the service is registered
    service = await mcp_service_service.get_service(db, event.service_id)
    if not service:
        raise HTTPException(
            status_code=400,
            detail=f"Service '{event.service_id}' not registered. "
                   "Register via POST /mcp/register first."
        )
    
    # Enqueue trigger for heartbeat delivery if agent is addressed
    if event.addressed_to:
        for target_agent in event.addressed_to:
            enqueue_trigger(target_agent, {
                "channel": event.topic,
                "sender": event.payload.get("sender", "unknown"),
                "text": event.payload.get("text", ""),
                "addressed_to": target_agent,
            })
    
    return {
        "status": "ok",
        "triggers_enqueued": len(event.addressed_to or [])
    }
