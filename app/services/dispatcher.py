"""Dispatcher — Routes jobs to agents (Redis) or MCP services (proxy).

Called as a FastAPI BackgroundTask after job creation.
Creates its own DB session so it outlives the request lifecycle.
"""

from app.db.session import AsyncSessionLocal
from app.services import router as job_router
from app.services import mcp_proxy
from app.services.job_service import get_job
from app.services.agent_registry import enqueue_trigger
from app.services.event_log import append_event
from app.exceptions import NoMCPServiceAvailable, MCPServiceTimeout, MCPServiceError
from app.queue import redis_queue


async def dispatch(job_id: str) -> None:
    """Entry point. Resolves target_type and dispatches accordingly."""
    async with AsyncSessionLocal() as db:
        job = await get_job(db, job_id)
        if not job:
            return

        if job.target_type == "agent":
            # If job is pre-assigned to a specific agent, use heartbeat trigger
            # Otherwise, enqueue in Redis for any agent to claim
            if job.assigned_agent:
                enqueue_trigger(job.assigned_agent, {
                    "job_id": job.job_id,
                    "channel": "motherbrain",
                    "sender": "system",
                    "text": f"Job assigned to you: {job.type} (id: {job.job_id})",
                    "addressed_to": job.assigned_agent,
                })
            else:
                await redis_queue.enqueue_job(job_id)

        elif job.target_type == "mcp":
            await _dispatch_mcp(db, job)


async def _dispatch_mcp(db, job) -> None:
    """Dispatch to an MCP service: route → proxy → store result."""
    # Mark as running
    job.status = "running"
    await db.commit()
    await db.refresh(job)

    try:
        route = await job_router.route_job(job, db)
        service = route["target"]
        result = await mcp_proxy.call_mcp_service(service, job)
        job.status = "completed"
        job.result = result
        job.error = None

    except (NoMCPServiceAvailable, MCPServiceTimeout, MCPServiceError) as e:
        job.status = "failed"
        job.error = str(e)
    except Exception as e:
        job.status = "failed"
        job.error = f"Unexpected error: {str(e)}"

    await db.commit()
    await db.refresh(job)

    # Log the proxy call to event log for audit
    await append_event(
        topic="proxy",
        service_id=job.target_service_id or "unknown",
        tool_name=job.type,
        arguments=job.payload or {},
        response=job.result if job.status == "completed" else {"error": job.error},
        status="ok" if job.status == "completed" else "error",
        duration_ms=0,
        agent_id=job.created_by or None,
    )

    await redis_queue.publish_event("job_updates", {
        "job_id": job.job_id,
        "status": job.status,
        "result": job.result,
        "error": job.error,
    })
