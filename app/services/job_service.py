"""Job Service — Business logic for job lifecycle management.

This module handles job creation, status updates, assignment, and querying.
Jobs can be assigned to agents or routed to MCP services based on target_type.

Extension Points:
    - Add job scheduling (delayed execution)
    - Add job retry logic with backoff
    - Add job cancellation
    - Add batch job operations
"""

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job
from app.schemas.job import JobCreate, JobStatusUpdate, NoteCreate


async def create_job(db: AsyncSession, job_create: JobCreate) -> Job:
    """Create a new job from the provided schema.
    
    The job starts with status "pending" and will be routed to an agent
    or MCP service based on target_type and requirements.
    """
    job = Job(
        type=job_create.type,
        payload=job_create.payload,
        requirements=job_create.requirements,
        parent_job=job_create.parent_job,
        depends_on=job_create.depends_on,
        priority=job_create.priority,
        notes=job_create.notes,
        created_by=job_create.created_by,
        target_type=job_create.target_type,
        target_service_id=job_create.target_service_id,
        topic=job_create.topic,
        assigned_agent=job_create.assigned_agent,
        context_job_ids=job_create.context_job_ids or [],
        skill_key=job_create.skill_key
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get_job(db: AsyncSession, job_id: str) -> Job | None:
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    return result.scalar_one_or_none()


async def update_status(db: AsyncSession, job_id: str, update: JobStatusUpdate) -> Job | None:
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if job:
        job.status = update.status
        await db.commit()
        await db.refresh(job)
    return job


async def assign_job(db: AsyncSession, job_id: str, agent_id: str) -> Job | None:
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if job:
        job.assigned_agent = agent_id
        job.status = "assigned"
        await db.commit()
        await db.refresh(job)
    return job


async def get_pending_jobs(db: AsyncSession) -> list[Job]:
    result = await db.execute(select(Job).where(Job.status == "pending"))
    return list(result.scalars().all())


async def list_jobs(db: AsyncSession, status: str | None = None, limit: int = 100) -> list[Job]:
    """List jobs with optional status filter."""
    query = select(Job)
    if status:
        query = query.where(Job.status == status)
    query = query.order_by(Job.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def add_child_job(db: AsyncSession, parent_id: str, child_id: str) -> Job | None:
    """Add a child job reference to the parent job."""
    result = await db.execute(select(Job).where(Job.job_id == parent_id))
    job = result.scalar_one_or_none()
    if job:
        if child_id not in job.child_jobs:
            job.child_jobs.append(child_id)
            await db.commit()
            await db.refresh(job)
    return job


async def add_note(db: AsyncSession, job_id: str, note: NoteCreate) -> Job | None:
    """Add a note to a job."""
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if job:
        note_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "author": note.author,
            "content": note.content
        }
        job.notes.append(note_entry)
        await db.commit()
        await db.refresh(job)
    return job


async def get_jobs_for_agent(db: AsyncSession, agent_id: str, status: str | None = None) -> list[Job]:
    """Get jobs assigned to a specific agent.
    
    Args:
        db: Database session
        agent_id: The agent's ID (e.g., "sampson", "motherbrain-agent")
        status: Optional status filter (pending, assigned, running, etc.)
    
    Returns:
        List of jobs assigned to this agent, ordered by creation time (newest first)
    """
    query = select(Job).where(Job.assigned_agent == agent_id)
    if status:
        query = query.where(Job.status == status)
    query = query.order_by(Job.created_at.desc()).limit(50)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_job_enriched(db: AsyncSession, job_id: str) -> dict | None:
    """Get a job with hydrated context references.
    
    Enriches the job with:
    - context_jobs: Full details of referenced prior jobs
    - skill: Full value from project_context for the skill_key
    
    Args:
        db: Database session
        job_id: The job ID to fetch
    
    Returns:
        Dict with job data + enriched context, or None if not found
    """
    from app.schemas.job import JobResponse, ContextJobInfo
    
    job = await get_job(db, job_id)
    if not job:
        return None
    
    # Build base job response
    job_data = JobResponse.model_validate(job).model_dump()
    
    # Hydrate context jobs (lightweight — id, type, status, result, payload only)
    context_jobs = []
    for cid in (job.context_job_ids or []):
        ctx_job = await get_job(db, cid)
        if ctx_job:
            context_jobs.append(ContextJobInfo(
                job_id=ctx_job.job_id,
                type=ctx_job.type,
                status=ctx_job.status,
                result=ctx_job.result,
                payload=ctx_job.payload
            ).model_dump())
    
    # Hydrate skill (bypass RBAC - if admin attached it, agent should receive it)
    skill = None
    if job.skill_key:
        from app.services.project_context_service import get_context
        ctx_entry = await get_context(db, job.skill_key, token=None)
        if ctx_entry:
            skill = ctx_entry.value
    
    return {
        **job_data,
        "context_jobs": context_jobs,
        "skill": skill
    }
