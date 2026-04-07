from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import verify_api_key, get_current_agent
from app.db.session import get_db
from app.schemas.agent import AgentCreate, AgentResponse, AgentRegistrationResponse, AgentStatusUpdate
from app.schemas.agent_action import AgentActionCreate
from app.schemas.job import JobResponse
from app.services import agent_service, job_service
from app.services.agent_action_service import create_action, get_actions_by_agent


router = APIRouter()


@router.post("/register", response_model=AgentRegistrationResponse)
async def register_agent(
    agent_create: AgentCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Register a new agent. Returns the agent including its auth token."""
    agent, plaintext_token = await agent_service.register_agent(db, agent_create)
    # Log the registration action
    await create_action(
        db,
        AgentActionCreate(
            agent_id=agent.agent_id,
            action_type="registered",
            job_id=None,
            details={"platform": agent.platform, "capabilities": agent.capabilities}
        )
    )
    # Return the response with the plaintext token (only time it's visible)
    return AgentRegistrationResponse(
        agent_id=agent.agent_id,
        name=agent.name,
        hostname=agent.hostname,
        platform=agent.platform,
        capabilities=agent.capabilities,
        status=agent.status,
        presence=agent.presence,
        last_heartbeat=agent.last_heartbeat,
        token=plaintext_token
    )


@router.post("/heartbeat")
async def heartbeat(
    db: AsyncSession = Depends(get_db),
    agent = Depends(get_current_agent)
):
    """Update agent heartbeat timestamp. Requires agent token."""
    updated = await agent_service.update_heartbeat(db, agent.agent_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "ok", "agent_id": agent.agent_id}


@router.get("/", response_model=list[AgentResponse])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """List all registered agents. Admin only."""
    agents = await agent_service.list_agents(db)
    return agents


@router.get("/by-name/{name}", response_model=AgentResponse)
async def get_agent_by_name_route(
    name: str,
    hostname: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get a specific agent by its name and optional hostname.
    
    This endpoint allows agents to check if they already exist
    without needing their authentication token. If hostname is
    provided, returns the specific agent on that machine.
    """
    if hostname:
        agent = await agent_service.get_agent_by_name_and_hostname(db, name, hostname)
    else:
        # Return first match if no hostname given
        agent = await agent_service.get_agent_by_name(db, name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/{agent_id}/jobs", response_model=list[JobResponse])
async def get_agent_jobs(
    agent_id: str,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get jobs assigned to a specific agent.
    
    Agents poll this endpoint to discover work addressed to them
    (e.g., via @mention in chat). Returns jobs newest first.
    
    Args:
        agent_id: The agent's unique ID (e.g., "sampson")
        status: Optional filter (pending, assigned, running, completed)
    
    Returns:
        List of jobs assigned to this agent
    """
    return await job_service.get_jobs_for_agent(db, agent_id, status)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get a specific agent by ID. Admin only."""
    agent = await agent_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/{agent_id}/actions")
async def get_agent_actions(
    agent_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get audit log actions for an agent. Admin only."""
    actions = await get_actions_by_agent(db, agent_id, limit)
    return actions


@router.post("/{agent_id}/status")
async def update_agent_status(
    agent_id: str,
    update: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Update agent status (online, offline, busy, etc). Admin only."""
    agent = await agent_service.update_agent_status(db, agent_id, update.status)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "ok", "agent_id": agent.agent_id, "new_status": update.status}
