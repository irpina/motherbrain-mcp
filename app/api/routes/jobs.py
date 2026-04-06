from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import verify_api_key, get_current_agent
from app.db.session import get_db
from app.schemas.job import JobCreate, JobResponse, JobStatusUpdate, LogEntry, NoteCreate
from app.services import job_service
from app.services.agent_action_service import create_action
from app.queue import redis_queue


router = APIRouter()


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """List all jobs with optional status filter. Admin only."""
    jobs = await job_service.list_jobs(db, status=status, limit=limit)
    return jobs


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_create: JobCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Create a new job and enqueue it. Admin only."""
    job = await job_service.create_job(db, job_create)
    await redis_queue.enqueue_job(job.job_id)
    return job


@router.get("/next", response_model=JobResponse)
async def get_next_job(
    db: AsyncSession = Depends(get_db),
    agent = Depends(get_current_agent)
):
    """Get the next available job from the queue. Requires agent token."""
    job_id = await redis_queue.dequeue_job()
    if not job_id:
        return Response(status_code=204)
    
    job = await job_service.get_job(db, job_id)
    if not job:
        # Re-enqueue the job if not found in DB to prevent loss
        await redis_queue.enqueue_job(job_id)
        return Response(status_code=204)
    
    # Assign the job to the requesting agent
    await job_service.assign_job(db, job_id, agent.agent_id)
    
    # Log the action
    from app.schemas.agent_action import AgentActionCreate
    await create_action(
        db,
        AgentActionCreate(
            agent_id=agent.agent_id,
            action_type="claimed_job",
            job_id=job_id,
            details={"job_type": job.type}
        )
    )
    
    return job


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get a job by ID. Admin only."""
    job = await job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/status", response_model=JobResponse)
async def update_job_status(
    job_id: str,
    update: JobStatusUpdate,
    db: AsyncSession = Depends(get_db),
    agent = Depends(get_current_agent)
):
    """Update job status and optionally append logs. Requires agent token."""
    job = await job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Verify the agent owns this job
    if job.assigned_agent != agent.agent_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this job")
    
    updated_job = await job_service.update_status(db, job_id, update)
    
    # Log the action
    from app.schemas.agent_action import AgentActionCreate
    action_type = f"{update.status}_job"
    await create_action(
        db,
        AgentActionCreate(
            agent_id=agent.agent_id,
            action_type=action_type,
            job_id=job_id,
            details={"log": update.log}
        )
    )
    
    # Publish event for real-time updates
    await redis_queue.publish_event("job_updates", {
        "job_id": job_id,
        "status": update.status,
        "log": update.log,
        "agent_id": agent.agent_id
    })
    
    return updated_job


@router.post("/{job_id}/logs")
async def append_job_logs(
    job_id: str,
    entry: LogEntry,
    _: str = Depends(get_current_agent)
):
    """Append logs to a job (stored in Redis). Requires agent token."""
    await redis_queue.append_log(job_id, entry.log)
    return {"status": "ok", "job_id": job_id}


@router.post("/{job_id}/notes", response_model=JobResponse)
async def add_job_note(
    job_id: str,
    note: NoteCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Add a note to a job. Admin only."""
    job = await job_service.add_note(db, job_id, note)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/child/{child_id}", response_model=JobResponse)
async def add_child_job(
    job_id: str,
    child_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Add a child job reference to a parent job. Admin only."""
    job = await job_service.add_child_job(db, job_id, child_id)
    if not job:
        raise HTTPException(status_code=404, detail="Parent job not found")
    return job
