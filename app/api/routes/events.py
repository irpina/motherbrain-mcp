"""Event API Routes — Generic event ingestion from MCP servers.

Any MCP server can POST events to this endpoint. Events become
pending jobs that the LLM discovers via GET /system/state.

This is the "Leg 1" of the loop: MCP server → Motherbrain.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_api_key
from app.db.session import get_db
from app.schemas.event import EventCreate
from app.schemas.job import JobCreate, JobResponse
from app.services import job_service
from app.services import mcp_service_service


router = APIRouter(tags=["events"])


@router.post("/events", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    event: EventCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Ingest an event from an MCP server.
    
    Any registered MCP server can POST events here. The event becomes
    a pending job that the LLM discovers via GET /system/state and
    can act upon.
    
    This is the app-agnostic event bus pattern — MCP servers push
    events to Motherbrain, Motherbrain stores them, LLM pulls and
    decides what to do.
    
    Args:
        event: The event to ingest
        db: Database session
    
    Returns:
        The created job (status=pending, waiting for LLM)
    
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
            "topic": "general"
        }
    
    Example response:
        {
            "job_id": "uuid",
            "type": "message_received",
            "payload": {...},
            "status": "pending",
            "target_type": "agent",
            "created_by": "agentchattr-mcp",
            "topic": "general",
            ...
        }
    """
    # Verify the service is registered
    service = await mcp_service_service.get_service(db, event.service_id)
    if not service:
        raise HTTPException(
            status_code=400,
            detail=f"Service '{event.service_id}' not registered. "
                   "Register via POST /mcp/register first."
        )
    
    # Create a job from the event
    # Events become jobs with target_type="agent" — the LLM will handle them
    job_create = JobCreate(
        type=event.event_type,
        payload=event.payload,
        requirements=[],  # LLM will figure out what's needed
        target_type="agent",  # Needs LLM intervention
        topic=event.topic,
        created_by=event.service_id,  # Track which service created this
    )
    
    job = await job_service.create_job(db, job_create)
    
    # Note: We don't dispatch via background task here.
    # Events from MCP services create jobs that sit as "pending"
    # until the LLM polls GET /system/state and decides what to do.
    
    return job
