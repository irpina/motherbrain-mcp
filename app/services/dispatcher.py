"""Dispatcher — Routes jobs to agents (Redis) or MCP services (proxy).

Called as a FastAPI BackgroundTask after job creation.
Creates its own DB session so it outlives the request lifecycle.
"""

from app.db.session import AsyncSessionLocal
from app.services import router as job_router
from app.services import mcp_proxy
from app.services.job_service import get_job
from app.exceptions import NoMCPServiceAvailable, MCPServiceTimeout, MCPServiceError
from app.queue import redis_queue


async def dispatch(job_id: str) -> None:
    """Entry point. Resolves target_type and dispatches accordingly."""
    async with AsyncSessionLocal() as db:
        job = await get_job(db, job_id)
        if not job:
            return

        if job.target_type == "agent":
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

    await redis_queue.publish_event("job_updates", {
        "job_id": job.job_id,
        "status": job.status,
        "result": job.result,
        "error": job.error,
    })
