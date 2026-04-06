"""System State Service — Aggregates full system state for LLM visibility.

This module provides a single source of truth for the current state of
the Motherbrain system, combining MCP services, jobs, agents, and recent
activity into one response.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import mcp_service_service, agent_service, job_service
from app.services.agent_action_service import get_recent_actions


async def get_system_state(db: AsyncSession, action_limit: int = 20) -> dict:
    """Aggregate full system state for LLM situational awareness.
    
    Returns a comprehensive snapshot including:
    - Registered MCP services and their status
    - Pending/running jobs that need attention
    - Online agents ready to work
    - Recent activity for context
    
    Args:
        db: Database session
        action_limit: Number of recent actions to include
    
    Returns:
        Dict with system state organized by category
    """
    # Gather data concurrently where possible
    mcp_services = await mcp_service_service.list_services(db)
    agents = await agent_service.list_agents(db)
    pending_jobs = await job_service.list_jobs(db, status="pending", limit=50)
    running_jobs = await job_service.list_jobs(db, status="running", limit=50)
    recent_actions = await get_recent_actions(db, limit=action_limit)
    
    # Build MCP summary
    mcp_summary = []
    for svc in mcp_services:
        mcp_summary.append({
            "service_id": svc.service_id,
            "name": svc.name,
            "endpoint": svc.endpoint,
            "status": svc.status,
            "protocol": svc.protocol,
            "capabilities": svc.capabilities or [],
            "last_heartbeat": svc.last_heartbeat.isoformat() if svc.last_heartbeat else None,
        })
    
    # Build agent summary
    agent_summary = []
    for agent in agents:
        # Calculate if agent is online (heartbeat within last 60s)
        is_online = False
        if agent.last_heartbeat:
            age = datetime.now(timezone.utc) - agent.last_heartbeat
            is_online = age < timedelta(seconds=60)
        
        agent_summary.append({
            "agent_id": agent.agent_id,
            "name": agent.name,
            "platform": agent.platform,
            "status": "online" if is_online else agent.status,
            "capabilities": agent.capabilities or {},
            "current_job": agent.current_job,
            "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
        })
    
    # Build job summary
    job_summary = []
    for job in pending_jobs + running_jobs:
        job_summary.append({
            "job_id": job.job_id,
            "type": job.type,
            "status": job.status,
            "target_type": job.target_type,
            "target_service_id": job.target_service_id,
            "assigned_agent": job.assigned_agent,
            "priority": job.priority,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        })
    
    # Build action summary
    action_summary = []
    for action in recent_actions:
        action_summary.append({
            "action_id": action.action_id,
            "agent_id": action.agent_id,
            "action_type": action.action_type,
            "job_id": action.job_id,
            "timestamp": action.timestamp.isoformat() if action.timestamp else None,
            "details": action.details,
        })
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mcp_services": {
            "count": len(mcp_services),
            "online": sum(1 for s in mcp_services if s.status == "online"),
            "services": mcp_summary,
        },
        "agents": {
            "count": len(agents),
            "online": sum(1 for a in agent_summary if a["status"] == "online"),
            "agents": agent_summary,
        },
        "jobs": {
            "pending": len(pending_jobs),
            "running": len(running_jobs),
            "jobs": job_summary,
        },
        "recent_activity": {
            "action_count": len(action_summary),
            "actions": action_summary,
        },
    }
